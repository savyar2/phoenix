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
    # Get fresh settings to ensure env vars are loaded
    current_settings = get_settings()
    if _openai_client is None and current_settings.openai_api_key:
        _openai_client = AsyncOpenAI(api_key=current_settings.openai_api_key)
        logger.info("OpenAI client initialized with service API key")
    return _openai_client


def get_anthropic_client() -> Optional[AsyncAnthropic]:
    """Get Anthropic client using service-provided API key."""
    global _anthropic_client
    if _anthropic_client is None and settings.anthropic_api_key:
        _anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        logger.info("Anthropic client initialized with service API key")
    return _anthropic_client


PROMPT_ANALYSIS_PROMPT = """Analyze this user prompt and determine:
1. What is the user's primary goal/intent?
2. What domains/categories are relevant? Choose from: shopping, eating, health, work, communication, personality, general
3. Are there any explicit preferences stated in the prompt that should override stored memory?

Output ONLY valid JSON with this structure:
{{
  "intent": "brief description of what user wants",
  "domains": ["list", "of", "relevant", "domains"],
  "explicit_preferences": ["any preferences explicitly stated in the prompt"],
  "keywords": ["key", "terms", "from", "prompt"]
}}

User prompt: "{prompt}"

Output ONLY the JSON, no other text:"""


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
Output: [{{"subject": "User", "subject_type": "Person", "predicate": "HAS_GOAL", "object": "Budget $50", "object_type": "Budget", "confidence": 0.9, "properties": {{"category": "Supplements", "timeframe": "monthly", "value": 50}}}}]

Input: "I started a vegan diet 3 days ago"
Output: [{{"subject": "User", "subject_type": "Person", "predicate": "HAS_CONSTRAINT", "object": "Vegan Diet", "object_type": "Diet", "confidence": 1.0, "properties": {{"started_days_ago": 3, "restriction": "no animal products"}}}}]

Input: "User browsed Steakhouse X on Yelp"
Output: [{{"subject": "User", "subject_type": "Person", "predicate": "INTERESTED_IN", "object": "Steakhouse X", "object_type": "Restaurant", "confidence": 0.6, "properties": {{"cuisine": "Steakhouse", "source": "Yelp"}}}}]

Now extract tuples from:
Input: "{context}"

Output ONLY the JSON array, no other text:"""


def _parse_llm_response(content: str) -> List[dict]:
    """Parse LLM response and extract JSON, ensuring it's always a list."""
    content = content.strip()
    
    # Try to extract JSON from response
    # Handle potential markdown code blocks
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0]
    elif '```' in content:
        parts = content.split('```')
        if len(parts) >= 2:
            content = parts[1]
    
    content = content.strip()
    
    try:
        data = json.loads(content)
        
        # Ensure we always return a list
        if isinstance(data, dict):
            # Single tuple returned, wrap in list
            if "tuples" in data:
                return data["tuples"]
            else:
                return [data]
        elif isinstance(data, list):
            return data
        else:
            return []
    except json.JSONDecodeError as e:
        # Try to find array or object in the content
        # Look for array
        arr_start = content.find('[')
        arr_end = content.rfind(']')
        if arr_start != -1 and arr_end != -1:
            try:
                return json.loads(content[arr_start:arr_end+1])
            except:
                pass
        
        # Look for object
        obj_start = content.find('{')
        obj_end = content.rfind('}')
        if obj_start != -1 and obj_end != -1:
            try:
                obj = json.loads(content[obj_start:obj_end+1])
                return [obj] if isinstance(obj, dict) else []
            except:
                pass
        
        raise e


def _convert_to_tuples(tuples_data: List[dict], source: str) -> List[SemanticTuple]:
    """Convert dict tuples to SemanticTuple objects."""
    tuples = []
    
    # Validate input
    if not isinstance(tuples_data, list):
        logger.warning(f"tuples_data is not a list: {type(tuples_data)}, converting")
        if isinstance(tuples_data, dict):
            tuples_data = [tuples_data]
        else:
            return []
    
    for i, t in enumerate(tuples_data):
        if not isinstance(t, dict):
            logger.warning(f"Tuple {i} is not a dict: {type(t)} = {t}")
            continue
            
        try:
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
        except Exception as e:
            logger.warning(f"Failed to convert tuple {i}: {e}")
            continue
            
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
            # Use standard completion (JSON mode requires object output, but we want array)
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
                logger.warning("OpenAI returned empty content")
                return None
            
            logger.info(f"OpenAI extraction response length: {len(content)}")
            
            # Parse the response
            try:
                parsed = _parse_llm_response(content)
                logger.info(f"Parsed {len(parsed)} tuples from OpenAI response")
                return parsed
            except Exception as parse_error:
                logger.warning(f"OpenAI response parse failed: {parse_error}, content: {content[:200]}")
                return None
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
    async def analyze_prompt(prompt: str) -> dict:
        """
        Analyze a user prompt to determine intent, relevant domains, and explicit preferences.
        Uses LLM to understand what the user wants and what context would be helpful.
        
        Returns:
            {
                "intent": str,
                "domains": List[str],
                "explicit_preferences": List[str],
                "keywords": List[str]
            }
        """
        client = get_openai_client()
        if not client:
            # Fallback to keyword-based analysis if no LLM available
            return Distiller._fallback_prompt_analysis(prompt)
        
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[{
                    'role': 'user',
                    'content': PROMPT_ANALYSIS_PROMPT.format(prompt=prompt)
                }],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if not content:
                return Distiller._fallback_prompt_analysis(prompt)
            
            # Clean up the response - strip and handle markdown code blocks
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Ensure result is a dict with expected structure
            if not isinstance(result, dict):
                logger.warning(f"LLM returned non-dict: {type(result)}")
                return Distiller._fallback_prompt_analysis(prompt)
            
            # Ensure domains is a list
            if "domains" not in result or not isinstance(result.get("domains"), list):
                result["domains"] = ["general", "communication", "personality"]
            
            logger.info(f"Analyzed prompt via LLM - intent: {result.get('intent')}, domains: {result.get('domains')}")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"Prompt analysis JSON parse failed: {e}, using fallback")
            return Distiller._fallback_prompt_analysis(prompt)
        except Exception as e:
            logger.warning(f"Prompt analysis failed: {e}, using fallback")
            return Distiller._fallback_prompt_analysis(prompt)
    
    @staticmethod
    def _fallback_prompt_analysis(prompt: str) -> dict:
        """Keyword-based fallback when LLM is unavailable."""
        prompt_lower = prompt.lower()
        domains = []
        keywords = prompt_lower.split()
        
        # Domain detection keywords
        domain_keywords = {
            "shopping": ["buy", "purchase", "price", "cost", "store", "shop", "product", "brand", "deal", "discount", "order", "amazon", "review", "rating", "cheap", "expensive", "quality", "return", "refund"],
            "eating": ["eat", "food", "restaurant", "meal", "cook", "recipe", "dinner", "lunch", "breakfast", "snack", "hungry", "cuisine", "diet", "taste", "delicious"],
            "health": ["health", "fitness", "exercise", "workout", "gym", "doctor", "medical", "symptom", "medicine", "sleep", "weight", "nutrition", "vitamin", "supplement"],
            "work": ["work", "job", "project", "meeting", "deadline", "email", "colleague", "office", "code", "programming", "finance", "budget", "career", "boss", "salary"],
        }
        
        for domain, kws in domain_keywords.items():
            if any(kw in prompt_lower for kw in kws):
                domains.append(domain)
        
        # Always include personality/communication for how to respond
        if not domains:
            domains = ["general"]
        
        # Always include these for response style
        domains.extend(["communication", "personality"])
        
        return {
            "intent": "user request",
            "domains": list(set(domains)),
            "explicit_preferences": [],
            "keywords": [w for w in keywords if len(w) > 3]
        }
    
    @staticmethod
    def check_conflicts(memory_text: str, prompt: str, explicit_preferences: List[str] = None) -> bool:
        """
        Check if a memory card conflicts with the user's prompt.
        
        Args:
            memory_text: The memory card text
            prompt: The original user prompt
            explicit_preferences: LLM-extracted explicit preferences (optional)
            
        Returns True if there's a conflict (memory should be excluded).
        """
        memory_lower = memory_text.lower()
        prompt_lower = prompt.lower()
        
        # Contradiction rules: (memory_contains, prompt_contains) -> conflict
        contradiction_rules = [
            # Price contradictions
            (["quality over", "prioritizes quality", "not the cheapest"], 
             ["cheapest", "lowest price", "budget", "affordable", "cheap"]),
            (["expensive", "premium", "luxury", "high-end"], 
             ["cheapest", "budget", "affordable", "cheap", "save money"]),
            (["cheap", "budget", "inexpensive", "affordable", "lowest price"], 
             ["premium", "luxury", "best quality", "money is no object", "price doesn't matter"]),
            
            # Options contradictions  
            (["few options", "curated", "best options picked"], 
             ["many options", "lots of choices", "browse", "show me everything", "all options"]),
            (["browsing lots", "many alternatives", "explore options"], 
             ["just pick one", "best option", "recommend one", "don't show me many"]),
            
            # Health/taste contradictions
            (["health", "nutrition", "healthy"], 
             ["taste", "comfort food", "indulgent", "delicious", "tasty"]),
            (["taste", "comfort", "indulgent"], 
             ["healthy", "nutritious", "diet", "low calorie"]),
            
            # Durability contradictions
            (["durable", "long-lasting", "quality"], 
             ["disposable", "temporary", "short-term", "one-time use"]),
            
            # Brand contradictions
            (["brand loyal", "stick to brands", "same brands"], 
             ["try new", "different brands", "alternatives", "variety"]),
            
            # Planning contradictions
            (["plans ahead", "decides before", "planned"], 
             ["spontaneous", "browse", "discover", "just looking"]),
        ]
        
        for memory_terms, prompt_terms in contradiction_rules:
            memory_matches = any(term in memory_lower for term in memory_terms)
            prompt_matches = any(term in prompt_lower for term in prompt_terms)
            
            if memory_matches and prompt_matches:
                logger.debug(f"Conflict detected: memory has {memory_terms}, prompt has {prompt_terms}")
                return True
        
        # Also check explicit preferences from LLM analysis
        if explicit_preferences:
            for pref in explicit_preferences:
                pref_lower = pref.lower()
                for memory_terms, pref_terms in contradiction_rules:
                    memory_matches = any(term in memory_lower for term in memory_terms)
                    pref_matches = any(term in pref_lower for term in pref_terms)
                    if memory_matches and pref_matches:
                        return True
        
        return False

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
