"""
Phoenix Protocol - LLM Distiller with Fallback

Extracts semantic tuples from raw user context.
Uses service-provided API keys (not user keys).
Tries cloud LLM (OpenAI/Claude) first, falls back to local Ollama.
"""
import structlog
import json
import asyncio
from typing import List, Optional
import ollama
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.config import get_settings
from app.models.tuples import SemanticTuple

logger = structlog.get_logger()
settings = get_settings()

# Initialize clients (lazy loading)
_openai_client: Optional[AsyncOpenAI] = None
_anthropic_client: Optional[AsyncAnthropic] = None


def get_openai_client() -> Optional[AsyncOpenAI]:
    """Get OpenAI client using service-provided API key."""
    global _openai_client
    if _openai_client is None and settings.openai_api_key:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI client initialized with service API key")
    return _openai_client


def get_anthropic_client() -> Optional[AsyncAnthropic]:
    """Get Anthropic client using service-provided API key."""
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        logger.info("Anthropic client initialized with service API key")
    return _anthropic_client


EXTRACTION_PROMPT = """You are a semantic tuple extractor. Given user behavior or statements, extract structured relationships.

Output ONLY valid JSON array of tuples. Each tuple has:
- subject: The entity performing or being described (usually "User")
- subject_type: Type of subject (Person, Product, etc.)
- predicate: The relationship (PREFERS, HAS_GOAL, HAS_CONSTRAINT, LIKES, DISLIKES, WANTS, AVOIDS)
- object: The target entity
- object_type: Type of object (Diet, Budget, Restaurant, Food, Product, etc.)
- confidence: 0.0 to 1.0 based on how certain the statement is
- properties: Additional key-value properties if relevant

Examples:

Input: "I'm trying to stay under $50 this month for protein powder"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "HAS_GOAL", "object": "Budget $50", "object_type": "Budget", "confidence": 0.9, "properties": {"category": "Supplements", "timeframe": "monthly", "value": 50}}]

Input: "I started a vegan diet 3 days ago"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "HAS_CONSTRAINT", "object": "Vegan Diet", "object_type": "Diet", "confidence": 1.0, "properties": {"started_days_ago": 3, "restriction": "no animal products"}}]

Input: "User browsed Steakhouse X on Yelp"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "INTERESTED_IN", "object": "Steakhouse X", "object_type": "Restaurant", "confidence": 0.6, "properties": {"cuisine": "Steakhouse", "source": "Yelp"}}]

Now extract tuples from:
Input: "{context}"

Output ONLY the JSON array, no other text:"""


def _parse_llm_response(content: str) -> List[dict]:
    """Parse LLM response and extract JSON."""
    content = content.strip()
    
    # Try to extract JSON from response
    # Handle potential markdown code blocks
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0]
    elif '```' in content:
        content = content.split('```')[1].split('```')[0]
    
    return json.loads(content)


def _convert_to_tuples(tuples_data: List[dict], source: str) -> List[SemanticTuple]:
    """Convert dict tuples to SemanticTuple objects."""
    tuples = []
    for t in tuples_data:
        tuples.append(SemanticTuple(
            subject=t.get('subject', 'User'),
            subject_type=t.get('subject_type', 'Person'),
            predicate=t.get('predicate', 'RELATES_TO'),
            object=t.get('object', ''),
            object_type=t.get('object_type', 'Entity'),
            confidence=t.get('confidence', 0.5),
            source=source,
            properties=t.get('properties', {})
        ))
    return tuples


class Distiller:
    """Extracts semantic tuples from raw context using LLM with fallback."""
    
    @staticmethod
    async def extract_tuples_with_openai(raw_context: str) -> Optional[List[dict]]:
        """Extract tuples using OpenAI with service-provided API key."""
        client = get_openai_client()
        if not client:
            logger.debug("OpenAI client not available (no service API key configured)")
            return None
        
        try:
            # Try with JSON mode first (for supported models)
            try:
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{
                        'role': 'user',
                        'content': EXTRACTION_PROMPT.format(context=raw_context)
                    }],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
            except Exception:
                # Fallback for models that don't support JSON mode
                response = await client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{
                        'role': 'user',
                        'content': EXTRACTION_PROMPT.format(context=raw_context)
                    }],
                    temperature=0.1,
                )
            
            content = response.choices[0].message.content
            if not content:
                return None
            
            # Try parsing as JSON object first (if using json_mode)
            try:
                data = json.loads(content)
                if isinstance(data, dict) and "tuples" in data:
                    return data["tuples"]
                elif isinstance(data, list):
                    return data
            except:
                pass
            
            # Fallback to text parsing
            return _parse_llm_response(content)
        except Exception as e:
            logger.warning(f"OpenAI extraction failed: {e}")
            return None
    
    @staticmethod
    async def extract_tuples_with_anthropic(raw_context: str) -> Optional[List[dict]]:
        """Extract tuples using Anthropic Claude with service-provided API key."""
        client = get_anthropic_client()
        if not client:
            logger.debug("Anthropic client not available (no service API key configured)")
            return None
        
        try:
            response = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=2000,
                messages=[{
                    'role': 'user',
                    'content': EXTRACTION_PROMPT.format(context=raw_context)
                }],
                temperature=0.1
            )
            
            content = response.content[0].text if response.content else None
            if not content:
                return None
            
            return _parse_llm_response(content)
        except Exception as e:
            logger.warning(f"Anthropic extraction failed: {e}")
            return None
    
    @staticmethod
    async def extract_tuples_with_ollama(raw_context: str) -> Optional[List[dict]]:
        """Extract tuples using local Ollama."""
        try:
            response = await asyncio.to_thread(
                ollama.chat,
                model=settings.ollama_model,
                messages=[{
                    'role': 'user',
                    'content': EXTRACTION_PROMPT.format(context=raw_context)
                }],
                options={
                    'temperature': 0.1,
                }
            )
            
            content = response['message']['content'].strip()
            return _parse_llm_response(content)
        except Exception as e:
            logger.warning(f"Ollama extraction failed: {e}")
            return None
    
    @staticmethod
    async def extract_tuples(raw_context: str, source: str = "manual") -> List[SemanticTuple]:
        """
        Extract semantic tuples from raw context.
        
        Uses service-provided API keys (not user keys).
        Tries providers in order:
        1. Cloud LLM (OpenAI or Anthropic based on preference)
        2. Local Ollama (if cloud fails or unavailable)
        """
        tuples_data = None
        provider_used = None
        
        # Determine provider order based on preference
        if settings.llm_provider_preference == "openai":
            providers = [
                ("openai", Distiller.extract_tuples_with_openai),
                ("anthropic", Distiller.extract_tuples_with_anthropic),
                ("ollama", Distiller.extract_tuples_with_ollama),
            ]
        elif settings.llm_provider_preference == "anthropic":
            providers = [
                ("anthropic", Distiller.extract_tuples_with_anthropic),
                ("openai", Distiller.extract_tuples_with_openai),
                ("ollama", Distiller.extract_tuples_with_ollama),
            ]
        else:  # ollama preference
            providers = [
                ("ollama", Distiller.extract_tuples_with_ollama),
                ("openai", Distiller.extract_tuples_with_openai),
                ("anthropic", Distiller.extract_tuples_with_anthropic),
            ]
        
        # Try each provider until one succeeds
        for provider_name, extract_func in providers:
            try:
                tuples_data = await extract_func(raw_context)
                if tuples_data:
                    provider_used = provider_name
                    logger.info(f"Successfully extracted tuples using {provider_name}")
                    break
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        if not tuples_data:
            logger.error("All LLM providers failed to extract tuples")
            return []
        
        # Convert to SemanticTuple objects
        tuples = _convert_to_tuples(tuples_data, source)
        logger.info(f"Extracted {len(tuples)} tuples from context using {provider_used}")
        return tuples
    
    @staticmethod
    async def health_check() -> dict:
        """Check availability of all LLM providers."""
        health = {
            "openai_available": False,
            "anthropic_available": False,
            "ollama_available": False,
        }
        
        # Check OpenAI (service-provided key)
        if settings.openai_api_key:
            client = get_openai_client()
            if client:
                try:
                    # Simple check - try to list models (lightweight)
                    await client.models.list()
                    health["openai_available"] = True
                except:
                    pass
        
        # Check Anthropic (service-provided key)
        if settings.anthropic_api_key:
            client = get_anthropic_client()
            if client:
                health["anthropic_available"] = True  # Anthropic doesn't have a lightweight check
        
        # Check Ollama
        try:
            await asyncio.to_thread(ollama.list)
            health["ollama_available"] = True
        except:
            pass
        
        return health
