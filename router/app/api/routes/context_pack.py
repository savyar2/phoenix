"""
Phoenix Protocol - Context Pack API Routes

Generates Context Packs for the Chrome extension to prepend to user prompts.
Uses LLM to analyze prompts and select relevant context.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import structlog

from app.models.memory_card import MemoryCard
from wallet.store.wallet_store import WalletStore
from app.config import get_settings
from app.services.distiller import Distiller
from app.services.graph_service import GraphService

router = APIRouter()
settings = get_settings()
logger = structlog.get_logger(__name__)

# Feature flag for Neo4j graph-based retrieval
USE_GRAPH_RETRIEVAL = True

# Initialize wallet store
_wallet_store: Optional[WalletStore] = None


def get_wallet_store() -> WalletStore:
    """Get or create wallet store instance."""
    global _wallet_store
    if _wallet_store is None:
        _wallet_store = WalletStore(
            db_path=str(settings.get_wallet_path()),
            encryption_key=settings.wallet_encryption_key
        )
    return _wallet_store


class ContextPackRequest(BaseModel):
    """Request for generating a context pack."""
    draft_prompt: str = Field(..., description="The user's draft prompt")
    site_id: str = Field(..., description="Site identifier (chatgpt, claude, gemini)")
    persona: str = Field(default="Personal", description="Active persona")
    sensitivity_mode: Literal["quiet", "verbose"] = Field(
        default="quiet", 
        description="How much context to show: quiet=minimal, verbose=detailed"
    )
    max_cards: int = Field(default=12, description="Maximum number of cards to include")
    min_relevance: float = Field(default=0.5, description="Minimum relevance score to include a card")


class UsedCard(BaseModel):
    """A memory card used in the context pack."""
    id: str
    type: str
    text: str
    domain: List[str]
    relevance_score: float = 1.0


class ContextPack(BaseModel):
    """The context pack to prepend to user prompts."""
    pack_text: str = Field(..., description="Formatted context to prepend")
    used_cards: List[UsedCard] = Field(default_factory=list, description="Cards used")
    card_count: int = Field(default=0)
    persona: str
    generated_at: str


class ContextPackResponse(BaseModel):
    """Response containing the context pack."""
    pack: ContextPack


def calculate_relevance(card: MemoryCard, prompt: str) -> float:
    """
    Calculate relevance score between a card and the prompt (legacy fallback).
    Personality/preference cards get a baseline score since they apply to all conversations.
    """
    prompt_lower = prompt.lower()
    score = 0.0
    
    # Baseline scores by card type - personality preferences always matter
    type_baselines = {
        "preference": 0.5,  # Preferences always somewhat relevant
        "constraint": 0.6,  # Constraints should always be respected
        "goal": 0.3,
        "capability": 0.2
    }
    score = type_baselines.get(card.type, 0.2)
    
    # Boost if profile-related (from answered questions)
    if "profile" in card.tags or "personality" in card.tags or "communication" in card.tags:
        score += 0.3
    
    # Check if any domain keywords appear in prompt
    for domain in card.domain:
        if domain.lower() in prompt_lower:
            score += 0.2
    
    # Check if any tags appear in prompt
    for tag in card.tags:
        if tag.lower() in prompt_lower:
            score += 0.15
    
    # Check for key words from card text in prompt
    card_words = set(card.text.lower().split())
    prompt_words = set(prompt_lower.split())
    common_words = card_words.intersection(prompt_words)
    
    # Exclude common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'to', 'for', 'of', 'in', 'on', 'and', 'or', 'i', 'my', 'me', 'user', 'prefers'}
    meaningful_common = [w for w in common_words if w not in stopwords and len(w) > 2]
    
    if meaningful_common:
        score += min(0.3, len(meaningful_common) * 0.1)
    
    # Boost hard constraints
    if card.priority == "hard":
        score += 0.2
    
    return min(1.0, score)


def calculate_smart_relevance(card: MemoryCard, relevant_domains: set, analysis: dict, prompt: str) -> float:
    """
    Calculate relevance score using LLM-analyzed domains AND text matching.
    
    Args:
        card: The memory card to score
        relevant_domains: Set of domains identified by LLM analysis
        analysis: Full analysis result from Distiller
        prompt: The original user prompt for text matching
        
    Returns:
        Relevance score 0.0 to 1.0
    """
    score = 0.0
    prompt_lower = prompt.lower()
    card_text_lower = card.text.lower()
    
    # 1. PRIORITY BOOST: Profile answers (from questions) have highest priority
    is_profile_card = "profile" in card.tags
    is_extracted_card = "extracted" in card.tags
    
    if is_profile_card:
        score += 0.3  # Profile answers get base boost
    
    # 2. DOMAIN MATCHING
    card_domains = set(d.lower() for d in card.domain)
    domain_overlap = card_domains.intersection(relevant_domains)
    
    if domain_overlap:
        score += 0.4 * (len(domain_overlap) / max(len(card_domains), 1))
    
    # 3. COMMUNICATION/PERSONALITY cards always relevant
    if "communication" in card_domains or "personality" in card_domains:
        score += 0.35
    
    # 4. TEXT CONTENT MATCHING - Check if prompt words appear in card text
    # This catches "pans" matching "cast iron pans", "iron" matching "cast iron"
    prompt_words = set(w for w in prompt_lower.split() if len(w) > 2)
    stopwords = {'the', 'a', 'an', 'is', 'are', 'to', 'for', 'of', 'in', 'on', 'and', 'or', 'find', 'me', 'some', 'get', 'best', 'good', 'how', 'what', 'why', 'when', 'where', 'can', 'should', 'would', 'could'}
    prompt_words = prompt_words - stopwords
    
    matches_found = 0
    for word in prompt_words:
        if word in card_text_lower:
            matches_found += 1
    
    if matches_found > 0:
        # Strong boost for text content match - scales with number of matches
        # This is the STRONGEST signal - user is asking about something specific
        score += min(0.8, 0.45 * matches_found)  # Up to 0.8 boost for multiple matches
    
    # 5. KEYWORD MATCHING from LLM analysis
    keywords = set(k.lower() for k in analysis.get("keywords", []))
    card_words = set(card_text_lower.split())
    keyword_matches = keywords.intersection(card_words)
    if keyword_matches:
        score += min(0.25, len(keyword_matches) * 0.08)
    
    # 6. TYPE-BASED SCORING
    if card.type == "constraint":
        score += 0.2
        if card.priority == "hard":
            score += 0.15
    
    # Extracted cards get slight penalty vs profile cards
    if is_extracted_card and not is_profile_card:
        score *= 0.9
    
    return min(1.0, score)


def check_card_conflicts(scored_cards: List[tuple]) -> List[tuple]:
    """
    Check for conflicts between cards and remove conflicting extracted cards.
    Profile cards override extracted cards when there's a conflict.
    
    Args:
        scored_cards: List of (card, score) tuples, already sorted by score
        
    Returns:
        Filtered list of (card, score) tuples with conflicts resolved, maintaining score order.
    """
    # Get all profile cards for conflict checking
    profile_cards = [card for card, _ in scored_cards if "profile" in card.tags]
    
    # Filter out conflicting extracted cards
    filtered = []
    for card, score in scored_cards:
        # Profile cards always pass
        if "profile" in card.tags:
            filtered.append((card, score))
            continue
        
        # Check if this extracted card conflicts with any profile card
        if "extracted" in card.tags:
            ext_text = card.text.lower()
            has_conflict = False
            
            for prof_card in profile_cards:
                prof_text = prof_card.text.lower()
                
                # Check for price/quality conflicts
                # Extracted card wants cheap/budget, but profile prioritizes quality
                ext_wants_cheap = ("cheapest" in ext_text or "cheap" in ext_text or "budget" in ext_text or "goal cheap" in ext_text)
                prof_prefers_quality = ("quality over" in prof_text or "prioritizes quality" in prof_text or "not the cheapest" in prof_text)
                
                if ext_wants_cheap and prof_prefers_quality:
                    logger.info(f"Conflict resolved: profile wins over extracted")
                    has_conflict = True
                    break
                
                # Check for quantity conflicts (lots of options vs curated)
                if (("lots" in ext_text or "many" in ext_text) and 
                    ("few" in prof_text or "curated" in prof_text)):
                    has_conflict = True
                    break
            
            if has_conflict:
                continue
        
        # Not an extracted card or no conflict - include it
        filtered.append((card, score))
    
    return filtered


async def get_graph_related_cards(tags: List[str], persona: str, wallet: WalletStore) -> List[MemoryCard]:
    """
    Use Neo4j graph to find related memory cards based on tags.
    Returns actual MemoryCard objects from the wallet.
    """
    try:
        # Query the graph for related memories
        graph_results = await GraphService.get_related_memories_by_tags(
            tags=tags,
            persona=persona,
            limit=20
        )
        
        if not graph_results:
            return []
        
        # Get the card IDs from graph results and fetch full cards from wallet
        all_wallet_cards = wallet.get_cards(persona=persona)
        card_map = {card.id: card for card in all_wallet_cards}
        
        related_cards = []
        for result in graph_results:
            card_id = result.get("id")
            if card_id and card_id in card_map:
                related_cards.append(card_map[card_id])
        
        logger.info(f"Found {len(related_cards)} cards via graph traversal")
        return related_cards
        
    except Exception as e:
        logger.warning(f"Graph retrieval failed, falling back to wallet: {e}")
        return []


def format_context_pack(cards: List[MemoryCard], persona: str) -> str:
    """Format memory cards into a context pack string."""
    if not cards:
        return ""
    
    lines = ["--- PERSONAL CONTEXT ---", ""]
    
    # Group by type
    constraints = [c for c in cards if c.type == "constraint"]
    preferences = [c for c in cards if c.type == "preference"]
    goals = [c for c in cards if c.type == "goal"]
    capabilities = [c for c in cards if c.type == "capability"]
    
    if constraints:
        lines.append("CONSTRAINTS:")
        for c in constraints:
            priority_marker = " [HARD]" if c.priority == "hard" else ""
            lines.append(f"• {c.text}{priority_marker}")
        lines.append("")
    
    if preferences:
        lines.append("PREFERENCES:")
        for p in preferences:
            lines.append(f"• {p.text}")
        lines.append("")
    
    if goals:
        lines.append("GOALS:")
        for g in goals:
            lines.append(f"• {g.text}")
        lines.append("")
    
    if capabilities:
        lines.append("CAPABILITIES:")
        for cap in capabilities:
            lines.append(f"• {cap.text}")
        lines.append("")
    
    lines.append("--- END PERSONAL CONTEXT ---")
    
    return "\n".join(lines)


@router.post("", response_model=ContextPackResponse)
async def generate_context_pack(request: ContextPackRequest):
    """
    Generate a context pack based on the user's draft prompt.
    
    Uses LLM to analyze the prompt and determine:
    1. What domains are relevant (shopping, health, work, etc.)
    2. What the user's intent is
    3. Any explicit preferences that should override memory
    
    The context pack contains relevant memory cards formatted as a header
    to prepend to the user's message.
    """
    try:
        wallet = get_wallet_store()
        
        # Get all cards for the persona
        all_cards = wallet.get_cards(persona=request.persona)
        
        logger.info(
            "Generating context pack",
            prompt_length=len(request.draft_prompt),
            persona=request.persona,
            total_cards=len(all_cards)
        )
        
        if not all_cards:
            # Return empty pack if no cards
            pack = ContextPack(
                pack_text="",
                used_cards=[],
                card_count=0,
                persona=request.persona,
                generated_at=datetime.utcnow().isoformat()
            )
            return ContextPackResponse(pack=pack)
        
        # STEP 1: Analyze the prompt using LLM
        analysis = await Distiller.analyze_prompt(request.draft_prompt)
        relevant_domains = set(analysis.get("domains", []))
        explicit_preferences = analysis.get("explicit_preferences", [])
        keywords = analysis.get("keywords", [])
        
        logger.info(
            "Prompt analyzed",
            intent=analysis.get("intent"),
            domains=list(relevant_domains),
            explicit_prefs=len(explicit_preferences),
            keywords=keywords
        )
        
        # STEP 2: Try graph-based retrieval first for smarter context
        graph_cards = []
        if USE_GRAPH_RETRIEVAL and keywords:
            # Combine domains and keywords for tag search
            search_tags = list(relevant_domains) + keywords
            graph_cards = await get_graph_related_cards(search_tags, request.persona, wallet)
        
        # Use ALL cards - graph retrieval is supplementary, not exclusive
        # This ensures we always check all memory cards for relevance
        candidate_cards = list(all_cards)  # Start with all cards
        logger.info(f"Starting with {len(candidate_cards)} wallet cards, graph returned {len(graph_cards)} cards")
        
        # STEP 3: Filter and score cards based on analysis
        scored_cards = []
        for card in candidate_cards:
            # Check for conflicts with explicit preferences and prompt keywords
            if Distiller.check_conflicts(card.text, request.draft_prompt, explicit_preferences):
                logger.info(f"Excluding card due to conflict with prompt: {card.text[:50]}")
                continue
            
            # Calculate relevance based on domain matching AND text content
            score = calculate_smart_relevance(card, relevant_domains, analysis, request.draft_prompt)
            
            
            # Only include cards above minimum relevance threshold
            if score >= request.min_relevance:
                scored_cards.append((card, score))
        
        # Sort by relevance
        scored_cards.sort(key=lambda x: x[1], reverse=True)
        
        # STEP 4: Resolve conflicts between profile and extracted cards
        # Pass the sorted scored_cards and get back filtered list maintaining order
        resolved_scored = check_card_conflicts(scored_cards)
        
        # Take all relevant cards up to max_cards limit
        top_cards = resolved_scored[:request.max_cards]
        
        logger.info(f"Selected {len(top_cards)} cards (from {len(scored_cards)} above threshold {request.min_relevance})")
        
        # Build used_cards list
        used_cards = [
            UsedCard(
                id=card.id,
                type=card.type,
                text=card.text,
                domain=card.domain,
                relevance_score=score
            )
            for card, score in top_cards
        ]
        
        # Format the pack text
        cards_only = [card for card, _ in top_cards]
        pack_text = format_context_pack(cards_only, request.persona)
        
        pack = ContextPack(
            pack_text=pack_text,
            used_cards=used_cards,
            card_count=len(used_cards),
            persona=request.persona,
            generated_at=datetime.utcnow().isoformat()
        )
        
        logger.info(
            "Context pack generated",
            cards_used=len(used_cards),
            pack_length=len(pack_text),
            domains_matched=list(relevant_domains)
        )
        
        return ContextPackResponse(pack=pack)
        
    except Exception as e:
        logger.error("Failed to generate context pack", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview")
async def preview_context_pack(
    persona: str = "Personal",
    max_cards: int = 5
):
    """
    Preview what context pack would be generated for a persona.
    Useful for the popup to show current context.
    """
    try:
        wallet = get_wallet_store()
        all_cards = wallet.get_cards(persona=persona)
        
        # Take first N cards (no prompt-based filtering)
        preview_cards = all_cards[:max_cards]
        
        pack_text = format_context_pack(preview_cards, persona)
        
        return {
            "success": True,
            "persona": persona,
            "total_cards": len(all_cards),
            "preview_cards": len(preview_cards),
            "pack_preview": pack_text,
            "cards": [
                {
                    "id": c.id,
                    "type": c.type,
                    "text": c.text[:100] + "..." if len(c.text) > 100 else c.text,
                    "domain": c.domain
                }
                for c in preview_cards
            ]
        }
    except Exception as e:
        logger.error("Failed to preview context pack", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph")
async def get_memory_graph(persona: str = "Personal", limit: int = 100):
    """
    Get the memory graph visualization data.
    
    Returns nodes (memory cards) and edges (shared tag relationships)
    for frontend visualization.
    """
    try:
        graph_data = await GraphService.get_memory_graph_visualization(
            persona=persona,
            limit=limit
        )
        
        return {
            "success": True,
            "persona": persona,
            "node_count": len(graph_data.get("nodes", [])),
            "edge_count": len(graph_data.get("edges", [])),
            "nodes": graph_data.get("nodes", []),
            "edges": graph_data.get("edges", [])
        }
    except Exception as e:
        logger.error("Failed to get memory graph", error=str(e))
        # Return empty graph if Neo4j is unavailable
        return {
            "success": False,
            "error": str(e),
            "persona": persona,
            "node_count": 0,
            "edge_count": 0,
            "nodes": [],
            "edges": []
        }

