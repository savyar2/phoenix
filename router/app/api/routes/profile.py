"""
Phoenix Protocol - Profile API Routes

Endpoints for managing user profiles, sub-profiles, questions, and answers.
"""
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from app.models.profile import (
    UserProfile, SubProfile, ProfileQuestion, ProfileAnswer,
    CreateProfileRequest, UpdateAnswerRequest, CreateSubProfileRequest, AddQuestionRequest,
    ConversationExtractionRequest, ConversationExtractionResponse
)
from app.config import get_settings
from wallet.store.wallet_store import WalletStore
from app.models.memory_card import MemoryCard
from app.services.graph_service import GraphService

router = APIRouter()
settings = get_settings()
logger = structlog.get_logger()


# In-memory storage (in production, use database)
_profiles: Dict[str, UserProfile] = {}


def get_default_main_questions() -> List[ProfileQuestion]:
    """Get the 12 default main profile questions for baseline AI context."""
    return [
        ProfileQuestion(
            question_text="Do you usually prefer people to be blunt and direct rather than diplomatic?",
            question_type="multiple_choice",
            options=["Blunt", "Neutral", "Diplomatic"],
            semantic_tags=["communication", "directness", "style"],
            order=1
        ),
        ProfileQuestion(
            question_text="Do you like getting the bottom line first before details?",
            question_type="multiple_choice",
            options=["Yes", "No"],
            semantic_tags=["communication", "details", "summary"],
            order=2
        ),
        ProfileQuestion(
            question_text="Do you trust a recommendation more when it includes the reasoning and tradeoffs, not just the answer?",
            question_type="multiple_choice",
            options=["Yes", "No"],
            semantic_tags=["recommendations", "reasoning", "tradeoffs", "decisions"],
            order=3
        ),
        ProfileQuestion(
            question_text="When learning, do you prefer examples over abstract explanations?",
            question_type="multiple_choice",
            options=["Examples", "Neutral", "Abstract"],
            semantic_tags=["learning", "examples", "explanations"],
            order=4
        ),
        ProfileQuestion(
            question_text="Do you get energized by lots of options, rather than overwhelmed by them?",
            question_type="multiple_choice",
            options=["Yes", "Neutral", "No"],
            semantic_tags=["options", "choices", "variety", "decisions"],
            order=5
        ),
        ProfileQuestion(
            question_text="Do you generally prefer a clear plan before you start, rather than figuring it out as you go?",
            question_type="multiple_choice",
            options=["Plan", "Neutral", "On the Fly"],
            semantic_tags=["planning", "structure", "spontaneity"],
            order=6
        ),
        ProfileQuestion(
            question_text="In disagreements, do you prefer to resolve things quickly rather than take time to cool off?",
            question_type="multiple_choice",
            options=["Quick", "Neutral", "Take Time"],
            semantic_tags=["conflict", "resolution", "timing"],
            order=7
        ),
        ProfileQuestion(
            question_text="If someone hurts your feelings, do you usually tell them directly rather than hint or withdraw?",
            question_type="multiple_choice",
            options=["Direct", "Neutral", "Hint"],
            semantic_tags=["communication", "emotions", "directness"],
            order=8
        ),
        ProfileQuestion(
            question_text="Do you find it easy to say 'no' without over-explaining?",
            question_type="multiple_choice",
            options=["Yes", "Neutral", "No"],
            semantic_tags=["boundaries", "communication", "assertiveness"],
            order=9
        ),
        ProfileQuestion(
            question_text="Do you prefer privacy and a small circle over being widely known and socially active?",
            question_type="multiple_choice",
            options=["Private", "Neutral", "Well-known"],
            semantic_tags=["privacy", "social", "personality"],
            order=10
        ),
        ProfileQuestion(
            question_text="Do you generally assume people mean well unless proven otherwise?",
            question_type="multiple_choice",
            options=["Yes", "Neutral", "No"],
            semantic_tags=["trust", "optimism", "people"],
            order=11
        ),
        ProfileQuestion(
            question_text="When you're stressed, do you become more quiet/internal rather than outward/talkative?",
            question_type="multiple_choice",
            options=["Quiet", "Neutral", "Talkative"],
            semantic_tags=["stress", "coping", "personality"],
            order=12
        ),
    ]


def get_default_sub_profiles() -> List[SubProfile]:
    """Get default sub-profiles with questions."""
    return [
        SubProfile(
            name="Shopping",
            description="Shopping preferences and habits",
            categories=["Electronics", "Clothing", "Groceries", "Books"],
            questions=[
                ProfileQuestion(
                    question_text="Do you usually decide what to buy before you enter the store/website?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["planning", "spontaneity", "browsing"]
                ),
                ProfileQuestion(
                    question_text="Do you typically choose the cheapest option if it seems 'good enough'?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["price", "budget", "cheap", "quality", "value"]
                ),
                ProfileQuestion(
                    question_text="Do you usually stick to the same brands once you find one you like?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["brands", "loyalty", "variety"]
                ),
                ProfileQuestion(
                    question_text="Do reviews/ratings influence you more than recommendations from friends/family?",
                    question_type="multiple_choice",
                    options=["Reviews", "Neutral", "Recs"],
                    semantic_tags=["reviews", "recommendations", "ratings", "trust"]
                ),
                ProfileQuestion(
                    question_text="Do you care more about long-term durability than immediate convenience?",
                    question_type="multiple_choice",
                    options=["Durable", "Neutral", "Convenience"],
                    semantic_tags=["durability", "quality", "convenience", "longevity"]
                ),
                ProfileQuestion(
                    question_text="For groceries, do you prioritize health/nutrition over taste/comfort?",
                    question_type="multiple_choice",
                    options=["Health", "Neutral", "Taste"],
                    semantic_tags=["health", "nutrition", "taste", "food", "groceries"]
                ),
                ProfileQuestion(
                    question_text="Do you actively look for deals (coupons, discounts, price comparisons) most of the time?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["deals", "discounts", "price", "budget", "savings"]
                ),
                ProfileQuestion(
                    question_text="Do you avoid products that feel wasteful (extra packaging, disposable, short lifespan)?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["sustainability", "waste", "environment", "packaging"]
                ),
                ProfileQuestion(
                    question_text="Do you return items easily if they aren't right, rather than keeping them?",
                    question_type="multiple_choice",
                    options=["Yes", "Neutral", "No"],
                    semantic_tags=["returns", "satisfaction", "decisions"]
                ),
                ProfileQuestion(
                    question_text="Do you prefer a few 'best' options picked for you over browsing lots of alternatives?",
                    question_type="multiple_choice",
                    options=["Few", "Neutral", "Many"],
                    semantic_tags=["options", "choices", "curation", "variety", "browsing"]
                ),
            ]
        ),
        SubProfile(
            name="Eating",
            description="Food preferences and dining habits",
            categories=["Restaurants", "Cooking", "Dietary", "Cuisines"],
            questions=[]
        ),
        SubProfile(
            name="Health",
            description="Health and wellness information",
            categories=["Fitness", "Medical", "Mental Health", "Nutrition"],
            questions=[]
        ),
        SubProfile(
            name="Work",
            description="Work and professional information",
            categories=["Finance", "Coding", "Projects", "Meetings"],
            questions=[]
        ),
    ]


def get_category_keywords(category: str) -> List[str]:
    """Get keywords for matching questions to categories."""
    keywords = {
        "Finance": ["finance", "budget", "money", "cost", "expense", "financial"],
        "Coding": ["code", "programming", "language", "developer", "software"],
        "Projects": ["project", "task", "deadline", "deliverable"],
        "Meetings": ["meeting", "call", "schedule", "calendar"],
        "Restaurants": ["restaurant", "dining", "eat out"],
        "Cooking": ["cook", "recipe", "kitchen"],
        "Dietary": ["diet", "restriction", "allergy", "vegan", "vegetarian"],
        "Cuisines": ["cuisine", "food type", "ethnic"],
        "Fitness": ["fitness", "exercise", "workout", "gym"],
        "Medical": ["medical", "doctor", "health", "symptom"],
        "Mental Health": ["mental", "therapy", "stress", "anxiety"],
        "Nutrition": ["nutrition", "supplement", "vitamin", "diet"]
    }
    return keywords.get(category, [])


def convert_profile_answer_to_memory_text(question_text: str, answer_text: str) -> str:
    """Convert a profile question+answer to semantic memory card text."""
    
    # Mapping of questions to semantic memory statements
    question_mappings = {
        "blunt and direct rather than diplomatic": {
            "Blunt": "User prefers blunt and direct communication over diplomatic language",
            "Neutral": "User is neutral about communication style - neither blunt nor diplomatic preference",
            "Diplomatic": "User prefers diplomatic and tactful communication over blunt directness"
        },
        "bottom line first before details": {
            "Yes": "User prefers getting the bottom line and conclusion first, before detailed explanations",
            "No": "User prefers detailed explanations before getting to the bottom line"
        },
        "reasoning and tradeoffs": {
            "Yes": "User trusts recommendations more when they include reasoning and tradeoffs, not just the answer",
            "No": "User prefers direct recommendations without lengthy reasoning or tradeoffs"
        },
        "examples over abstract explanations": {
            "Examples": "User learns better through concrete examples rather than abstract explanations",
            "Neutral": "User is flexible with both examples and abstract explanations when learning",
            "Abstract": "User prefers abstract explanations and concepts over concrete examples"
        },
        "energized by lots of options": {
            "Yes": "User gets energized by having lots of options to choose from",
            "Neutral": "User is neutral about the number of options presented",
            "No": "User gets overwhelmed by too many options and prefers fewer choices"
        },
        "clear plan before you start": {
            "Plan": "User prefers having a clear plan before starting any task",
            "Neutral": "User is flexible between planning ahead and figuring things out as they go",
            "On the Fly": "User prefers figuring things out as they go rather than planning ahead"
        },
        "resolve things quickly": {
            "Quick": "In disagreements, user prefers to resolve things quickly",
            "Neutral": "User is flexible about timing when resolving disagreements",
            "Take Time": "In disagreements, user prefers taking time to cool off before resolving"
        },
        "tell them directly rather than hint": {
            "Direct": "When feelings are hurt, user prefers to tell people directly",
            "Neutral": "User is flexible in how they communicate hurt feelings",
            "Hint": "When feelings are hurt, user prefers to hint or withdraw rather than be direct"
        },
        "easy to say 'no'": {
            "Yes": "User finds it easy to say 'no' without over-explaining",
            "Neutral": "User is neutral about saying 'no' - sometimes easy, sometimes not",
            "No": "User finds it difficult to say 'no' without feeling the need to over-explain"
        },
        "privacy and a small circle": {
            "Private": "User prefers privacy and a small social circle",
            "Neutral": "User is flexible between privacy and social activity",
            "Well-known": "User prefers being widely known and socially active"
        },
        "assume people mean well": {
            "Yes": "User generally assumes people mean well unless proven otherwise",
            "Neutral": "User is cautiously neutral about people's intentions",
            "No": "User does not assume people mean well until they prove themselves"
        },
        "quiet/internal rather than outward": {
            "Quiet": "When stressed, user becomes more quiet and internal",
            "Neutral": "User's behavior under stress is variable",
            "Talkative": "When stressed, user becomes more outward and talkative"
        },
        # Shopping profile questions
        "decide what to buy before you enter": {
            "Yes": "User typically decides what to buy before entering stores or websites",
            "Neutral": "User sometimes plans purchases and sometimes browses spontaneously",
            "No": "User prefers browsing and discovering what to buy in the moment"
        },
        "cheapest option if it seems 'good enough'": {
            "Yes": "User typically chooses the cheapest option when quality seems adequate",
            "Neutral": "User balances price and quality without strong preference for cheapest",
            "No": "User prioritizes quality over getting the cheapest option"
        },
        "stick to the same brands": {
            "Yes": "User is brand loyal and sticks to brands they like",
            "Neutral": "User is flexible between familiar brands and trying new ones",
            "No": "User likes to try different brands rather than sticking to one"
        },
        "reviews/ratings influence you more than recommendations": {
            "Reviews": "User trusts online reviews and ratings more than personal recommendations",
            "Neutral": "User values both reviews and personal recommendations equally",
            "Recs": "User trusts recommendations from friends and family more than online reviews"
        },
        "long-term durability than immediate convenience": {
            "Durable": "User prioritizes long-term durability over immediate convenience when shopping",
            "Neutral": "User balances durability and convenience based on the product",
            "Convenience": "User prioritizes immediate convenience over long-term durability"
        },
        "prioritize health/nutrition over taste/comfort": {
            "Health": "For groceries, user prioritizes health and nutrition over taste",
            "Neutral": "User balances health and taste when shopping for groceries",
            "Taste": "For groceries, user prioritizes taste and comfort over health considerations"
        },
        "actively look for deals": {
            "Yes": "User actively hunts for deals, coupons, and price comparisons",
            "Neutral": "User sometimes looks for deals but doesn't prioritize it",
            "No": "User doesn't spend much effort on finding deals or discounts"
        },
        "avoid products that feel wasteful": {
            "Yes": "User avoids wasteful products (excess packaging, disposable, short lifespan)",
            "Neutral": "User considers sustainability but it's not a top priority",
            "No": "User doesn't strongly consider wastefulness when shopping"
        },
        "return items easily if they aren't right": {
            "Yes": "User returns items easily when they aren't right",
            "Neutral": "User sometimes returns items but often keeps things even if not perfect",
            "No": "User tends to keep items even if they aren't quite right rather than return"
        },
        "few 'best' options picked for you": {
            "Few": "User prefers having a few curated 'best' options rather than many alternatives",
            "Neutral": "User is flexible between curated picks and browsing many options",
            "Many": "User prefers browsing lots of alternatives rather than curated recommendations"
        }
    }
    
    # Find matching question pattern
    question_lower = question_text.lower()
    for pattern, answers_map in question_mappings.items():
        if pattern in question_lower:
            if answer_text in answers_map:
                return answers_map[answer_text]
    
    # Fallback: generic conversion
    return f"User preference: {question_text} - {answer_text}"


@router.post("/create")
async def create_profile(request: CreateProfileRequest):
    """Create a new user profile with default questions."""
    if request.user_id in _profiles:
        raise HTTPException(status_code=400, detail="Profile already exists")
    
    profile = UserProfile(
        user_id=request.user_id,
        main_questions=get_default_main_questions(),
        sub_profiles=get_default_sub_profiles()
    )
    
    _profiles[request.user_id] = profile
    
    return {
        "success": True,
        "profile": profile,
        "message": "Profile created successfully"
    }


@router.get("/{user_id}")
async def get_profile(user_id: str):
    """Get user profile."""
    if user_id not in _profiles:
        # Auto-create if doesn't exist
        profile = UserProfile(
            user_id=user_id,
            main_questions=get_default_main_questions(),
            sub_profiles=get_default_sub_profiles()
        )
        _profiles[user_id] = profile
    else:
        profile = _profiles[user_id]
    
    return {
        "success": True,
        "profile": profile
    }


@router.post("/{user_id}/answer")
async def update_answer(user_id: str, request: UpdateAnswerRequest):
    """Update an answer to a question and automatically create memory card (direct conversion, no Distiller)."""
    if user_id not in _profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = _profiles[user_id]
    
    # Find the question
    question = None
    sub_profile = None
    
    # Check main questions first
    for q in profile.main_questions:
        if q.id == request.question_id:
            question = q
            break
    
    # Check sub-profiles if not found
    if not question:
        for sp in profile.sub_profiles:
            for q in sp.questions:
                if q.id == request.question_id:
                    question = q
                    sub_profile = sp
                    break
            if question:
                break
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Find existing answer or create new
    answer = None
    if not sub_profile:
        # Main profile answer
        for ans in profile.main_answers:
            if ans.question_id == request.question_id:
                answer = ans
                break
        
        if answer:
            answer.answer_text = request.answer_text
            answer.answer_data = request.answer_data
            answer.updated_at = datetime.utcnow()
        else:
            answer = ProfileAnswer(
                question_id=request.question_id,
                answer_text=request.answer_text,
                answer_data=request.answer_data
            )
            profile.main_answers.append(answer)
    else:
        # Sub-profile answer
        for ans in sub_profile.answers:
            if ans.question_id == request.question_id:
                answer = ans
                break
        
        if answer:
            answer.answer_text = request.answer_text
            answer.answer_data = request.answer_data
            answer.updated_at = datetime.utcnow()
        else:
            answer = ProfileAnswer(
                question_id=request.question_id,
                answer_text=request.answer_text,
                answer_data=request.answer_data
            )
            sub_profile.answers.append(answer)
    
    profile.updated_at = datetime.utcnow()
    
    # DIRECTLY CREATE MEMORY CARD (hardcoded, no Distiller)
    # Only create if this is a NEW answer (not an update)
    try:
        wallet = WalletStore(
            db_path=str(settings.get_wallet_path()),
            encryption_key=settings.wallet_encryption_key
        )
        
        question_lower = question.question_text.lower()
        
        # Generate the memory text first so we can check for duplicates
        memory_text = convert_profile_answer_to_memory_text(question.question_text, request.answer_text)
        
        # Check if we already have a card for this question (avoid duplicates)
        existing_cards = wallet.get_cards(persona="Personal")
        for existing_card in existing_cards:
            # Check if the card has matching text (same question answered before)
            if existing_card.text[:50].lower() == memory_text[:50].lower():
                wallet.delete_card(existing_card.id)
                logger.info(f"Deleted existing card {existing_card.id} to replace with updated answer")
                break
        
        # Determine memory card type from question context
        card_type = "preference"  # default for most profile questions
        if "restriction" in question_lower or "constraint" in question_lower or "cannot" in question_lower:
            card_type = "constraint"
        elif "goal" in question_lower or "aspiration" in question_lower or "want" in question_lower:
            card_type = "goal"
        elif "capability" in question_lower or "can" in question_lower or "skill" in question_lower:
            card_type = "capability"
        
        # Determine domain from question/sub-profile context
        domain = []
        if sub_profile:
            domain.append(sub_profile.name.lower())
            # Add categories if available
            if sub_profile.categories:
                # Try to match question to category
                for cat in sub_profile.categories:
                    if cat.lower() in question_lower or any(kw in question_lower for kw in get_category_keywords(cat)):
                        domain.append(cat.lower())
        else:
            # Main profile question - determine domain based on content
            if "work" in question_lower or "occupation" in question_lower or "job" in question_lower:
                domain = ["work"]
            elif "food" in question_lower or "diet" in question_lower or "eating" in question_lower or "meal" in question_lower:
                domain = ["eating", "food"]
            elif "health" in question_lower or "fitness" in question_lower or "exercise" in question_lower:
                domain = ["health"]
            elif "shopping" in question_lower or "budget" in question_lower or "purchase" in question_lower:
                domain = ["shopping"]
            # Main profile personality/communication questions
            elif any(kw in question_lower for kw in ["prefer", "communication", "blunt", "diplomatic", "bottom line", 
                     "reasoning", "learning", "examples", "options", "plan", "disagreement", 
                     "feelings", "say no", "privacy", "assume", "stressed"]):
                domain = ["communication", "personality"]
            else:
                domain = ["general"]
        
        # Create memory card directly from answer (memory_text already computed above)
        # Include the question's semantic tags for cross-profile matching
        all_tags = ["profile"] + (domain if domain else [])
        if hasattr(question, 'semantic_tags') and question.semantic_tags:
            all_tags.extend(question.semantic_tags)
        
        card = MemoryCard(
            type=card_type,
            text=memory_text,
            domain=domain if domain else ["general"],
            priority="soft",
            tags=list(set(all_tags)),  # Deduplicate tags
            persona="Personal"
        )
        
        saved_card = wallet.add_card(card)
        logger.info(f"Created memory card {saved_card.id} from profile answer", user_id=user_id, question_id=request.question_id)
        
        # Add to Neo4j graph for relationship tracking
        try:
            await GraphService.add_memory_card_to_graph(
                card_id=saved_card.id,
                card_text=saved_card.text,
                card_type=saved_card.type,
                domain=saved_card.domain,
                tags=saved_card.tags,
                persona=saved_card.persona
            )
            logger.info(f"Added memory card {saved_card.id} to graph", user_id=user_id)
        except Exception as graph_error:
            logger.warning(f"Failed to add memory card to graph: {graph_error}", user_id=user_id)
            # Don't fail if graph is unavailable
    except Exception as e:
        logger.error(f"Failed to create memory card from profile answer: {e}", user_id=user_id)
        # Don't fail the request if memory card creation fails
    
    return {
        "success": True,
        "answer": answer,
        "message": "Answer updated successfully"
    }


@router.post("/{user_id}/sub-profile")
async def create_sub_profile(user_id: str, request: CreateSubProfileRequest):
    """Create a new sub-profile."""
    if user_id not in _profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = _profiles[user_id]
    
    sub_profile = SubProfile(
        name=request.name,
        description=request.description,
        categories=request.categories
    )
    
    profile.sub_profiles.append(sub_profile)
    profile.updated_at = datetime.utcnow()
    
    return {
        "success": True,
        "sub_profile": sub_profile,
        "message": "Sub-profile created successfully"
    }


@router.post("/{user_id}/question")
async def add_question(user_id: str, request: AddQuestionRequest):
    """Add a question to main profile or sub-profile."""
    if user_id not in _profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = _profiles[user_id]
    
    question = ProfileQuestion(
        question_text=request.question_text,
        question_type=request.question_type,
        options=request.options,
        required=request.required,
        order=request.order
    )
    
    if request.sub_profile_id:
        # Add to sub-profile
        for sub_profile in profile.sub_profiles:
            if sub_profile.id == request.sub_profile_id:
                sub_profile.questions.append(question)
                sub_profile.updated_at = datetime.utcnow()
                break
        else:
            raise HTTPException(status_code=404, detail="Sub-profile not found")
    else:
        # Add to main profile
        profile.main_questions.append(question)
    
    profile.updated_at = datetime.utcnow()
    
    return {
        "success": True,
        "question": question,
        "message": "Question added successfully"
    }


@router.post("/{user_id}/extract", response_model=ConversationExtractionResponse)
async def extract_conversation(user_id: str, request: ConversationExtractionRequest):
    """
    Extract information from ChatGPT/Gemini conversation using Distiller.
    
    This endpoint:
    1. Uses Distiller to extract semantic tuples from conversation
    2. Categorizes tuples into sub-profiles
    3. Creates memory cards from extracted tuples
    
    NOTE: Profile answers are handled separately (direct conversion, no Distiller).
    """
    try:
        from app.services.extraction_service import ExtractionService
        
        # STEP 1: Extract using enhanced service (uses Distiller internally)
        result = await ExtractionService.extract_from_conversation(
            conversation_text=request.conversation_text,
            messages=request.messages,
            user_id=user_id
        )
        
        # STEP 2: Convert extracted items to memory cards
        wallet = WalletStore(
            db_path=str(settings.get_wallet_path()),
            encryption_key=settings.wallet_encryption_key
        )
        
        cards_created = []
        for item in result["extracted_items"]:
            # Determine domain from category
            domain = [item["category"].lower()]
            if item.get("sub_category"):
                domain.append(item["sub_category"].lower())
            
            # Build tags for the card - include content-based keywords
            tags = ["extracted", item["category"].lower()]
            if item.get("sub_category"):
                tags.append(item["sub_category"].lower())
            
            # Extract key content words as tags for better matching
            stopwords = {'user', 'the', 'a', 'an', 'is', 'are', 'to', 'for', 'of', 'in', 'on', 'and', 'or', 'likes', 'prefers', 'has_goal', 'avoids', 'wants'}
            text_words = item["text"].lower().split()
            content_tags = [w for w in text_words if len(w) > 3 and w not in stopwords][:5]  # Top 5 content words
            tags.extend(content_tags)
            
            # Extract from properties if available (e.g., material: ["cast iron", "carbon steel"])
            props = item.get("properties", {})
            for key, val in props.items():
                if isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            tags.extend(v.lower().split())
                elif isinstance(val, str):
                    tags.extend(val.lower().split())
            
            # Deduplicate tags
            tags = list(set(tags))
            
            card = MemoryCard(
                type=item.get("type", "preference"),
                text=item["text"],
                domain=domain,
                priority="soft",  # Extracted items have lower priority than profile answers
                tags=tags,
                persona="Personal"
            )
            saved_card = wallet.add_card(card)
            cards_created.append(saved_card.id)
            
            # Add to Neo4j graph for relationship tracking
            try:
                await GraphService.add_memory_card_to_graph(
                    card_id=saved_card.id,
                    card_text=saved_card.text,
                    card_type=saved_card.type,
                    domain=saved_card.domain,
                    tags=saved_card.tags,
                    persona=saved_card.persona
                )
            except Exception as graph_error:
                logger.warning(f"Failed to add extracted card to graph: {graph_error}")
        
        logger.info(
            "Extracted conversation and created memory cards",
            user_id=user_id,
            cards_created=len(cards_created)
        )
        
        return ConversationExtractionResponse(
            success=True,
            extracted_items=result["extracted_items"],
            categorized=result["categorized"],
            memory_cards_created=len(cards_created),
            message=f"Extracted {len(result['extracted_items'])} items and created {len(cards_created)} memory cards"
        )
    except Exception as e:
        logger.error(f"Failed to extract conversation: {e}", user_id=user_id)
        raise HTTPException(status_code=500, detail=str(e))

