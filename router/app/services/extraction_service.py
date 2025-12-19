"""
Phoenix Protocol - Conversation Extraction Service

Extracts relevant information from conversations and categorizes into sub-profiles.
Uses Distiller for LLM-based extraction.
"""
import structlog
from typing import List, Dict, Optional
import json

from app.config import get_settings
from app.services.distiller import Distiller

logger = structlog.get_logger()
settings = get_settings()


class ExtractionService:
    """Service for extracting and categorizing information from conversations."""
    
    @classmethod
    async def extract_from_conversation(
        cls,
        conversation_text: str,
        messages: List[Dict],
        user_id: str
    ) -> Dict:
        """
        Extract relevant information from ChatGPT/Gemini conversations using LLM.
        
        NOTE: Profile answers use direct conversion (no Distiller).
        This service is ONLY for conversation extraction.
        
        Args:
            conversation_text: Full conversation text
            messages: Structured message list
            user_id: User identifier
        
        Returns:
            Dictionary with extracted items and categorization
        """
        try:
            # USE DISTILLER to extract semantic tuples from conversation
            tuples = await Distiller.extract_tuples(conversation_text, source="conversation")
            
            extracted_items = []
            categorized = {
                "Shopping": [],
                "Eating": [],
                "Health": [],
                "Work": [],
                "Work_Finance": [],
                "Work_Coding": [],
                "Work_Projects": [],
                "Work_Meetings": [],
                "General": []
            }
            
            # Categorize tuples into sub-profiles
            for tuple_data in tuples:
                item = {
                    "type": cls._tuple_to_card_type(tuple_data.predicate),
                    "text": f"{tuple_data.subject} {tuple_data.predicate} {tuple_data.object}",
                    "category": cls._categorize_tuple(tuple_data),
                    "sub_category": cls._get_work_subcategory(tuple_data) if cls._categorize_tuple(tuple_data) == "Work" else None,
                    "confidence": tuple_data.confidence,
                    "properties": tuple_data.properties
                }
                
                extracted_items.append(item)
                
                # Add to categorized structure (flattened)
                category = item["category"]
                if category == "Work" and item["sub_category"]:
                    sub_key = f"Work_{item['sub_category']}"
                    if sub_key in categorized:
                        categorized[sub_key].append(item)
                    else:
                        categorized["Work_Projects"].append(item)  # Default
                elif category in categorized:
                    categorized[category].append(item)
                else:
                    categorized["General"].append(item)
            
            logger.info(
                "Extracted information from conversation",
                user_id=user_id,
                items_count=len(extracted_items),
                tuples_count=len(tuples)
            )
            
            return {
                "extracted_items": extracted_items,
                "categorized": categorized
            }
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}", user_id=user_id)
            # Fallback to keyword-based extraction
            return cls._keyword_based_extraction(conversation_text, user_id)
    
    @classmethod
    def _tuple_to_card_type(cls, predicate: str) -> str:
        """Convert tuple predicate to memory card type."""
        if "CONSTRAINT" in predicate:
            return "constraint"
        elif "GOAL" in predicate:
            return "goal"
        elif "PREFERS" in predicate or "LIKES" in predicate:
            return "preference"
        else:
            return "preference"
    
    @classmethod
    def _categorize_tuple(cls, tuple_data) -> str:
        """Categorize tuple into sub-profile."""
        obj_type = tuple_data.object_type.lower()
        text = f"{tuple_data.object} {tuple_data.predicate}".lower()
        
        if any(kw in obj_type or kw in text for kw in ["shop", "purchase", "buy", "product", "shopping"]):
            return "Shopping"
        elif any(kw in obj_type or kw in text for kw in ["food", "restaurant", "meal", "dining", "diet", "eating", "cuisine"]):
            return "Eating"
        elif any(kw in obj_type or kw in text for kw in ["health", "fitness", "medical", "exercise", "wellness"]):
            return "Health"
        elif any(kw in obj_type or kw in text for kw in ["work", "project", "code", "finance", "meeting", "professional"]):
            return "Work"
        else:
            return "Shopping"  # Default
    
    @classmethod
    def _get_work_subcategory(cls, tuple_data) -> str:
        """Get work sub-category."""
        text = f"{tuple_data.object} {tuple_data.predicate}".lower()
        if any(kw in text for kw in ["finance", "budget", "money", "cost", "expense", "financial"]):
            return "Finance"
        elif any(kw in text for kw in ["code", "programming", "language", "function", "algorithm", "coding", "developer"]):
            return "Coding"
        elif any(kw in text for kw in ["meeting", "call", "schedule", "calendar", "appointment"]):
            return "Meetings"
        else:
            return "Projects"
    
    @classmethod
    def _keyword_based_extraction(cls, text: str, user_id: str) -> Dict:
        """Fallback keyword-based extraction."""
        extracted_items = []
        categorized = {
            "Shopping": [],
            "Eating": [],
            "Health": [],
            "Work": [],
            "Work_Finance": [],
            "Work_Coding": [],
            "Work_Projects": [],
            "Work_Meetings": [],
            "General": []
        }
        
        text_lower = text.lower()
        
        # Shopping keywords
        shopping_keywords = ["buy", "purchase", "shop", "order", "product", "price", "cost", "budget", "shopping"]
        if any(kw in text_lower for kw in shopping_keywords):
            extracted_items.append({
                "type": "preference",
                "text": cls._extract_relevant_snippet(text, shopping_keywords),
                "category": "Shopping",
                "confidence": 0.7
            })
            categorized["Shopping"].append(extracted_items[-1])
        
        # Eating keywords
        eating_keywords = ["restaurant", "food", "meal", "dinner", "lunch", "breakfast", "eat", "dining", "cuisine", "diet"]
        if any(kw in text_lower for kw in eating_keywords):
            extracted_items.append({
                "type": "preference",
                "text": cls._extract_relevant_snippet(text, eating_keywords),
                "category": "Eating",
                "confidence": 0.7
            })
            categorized["Eating"].append(extracted_items[-1])
        
        # Health keywords
        health_keywords = ["health", "fitness", "exercise", "workout", "medical", "doctor", "symptom", "medication", "supplement"]
        if any(kw in text_lower for kw in health_keywords):
            extracted_items.append({
                "type": "preference",
                "text": cls._extract_relevant_snippet(text, health_keywords),
                "category": "Health",
                "confidence": 0.7
            })
            categorized["Health"].append(extracted_items[-1])
        
        # Work keywords
        work_keywords = ["work", "project", "code", "programming", "meeting", "finance", "budget", "deadline", "task"]
        if any(kw in text_lower for kw in work_keywords):
            snippet = cls._extract_relevant_snippet(text, work_keywords)
            item = {
                "type": "preference",
                "text": snippet,
                "category": "Work",
                "confidence": 0.7
            }
            extracted_items.append(item)
            
            # Categorize into work sub-categories (flattened keys)
            snippet_lower = snippet.lower()
            if any(kw in snippet_lower for kw in ["finance", "budget", "money", "cost", "expense"]):
                categorized["Work_Finance"].append(item)
            elif any(kw in snippet_lower for kw in ["code", "programming", "language", "function", "algorithm"]):
                categorized["Work_Coding"].append(item)
            elif any(kw in snippet_lower for kw in ["project", "task", "deadline", "deliverable"]):
                categorized["Work_Projects"].append(item)
            elif any(kw in snippet_lower for kw in ["meeting", "call", "schedule", "calendar"]):
                categorized["Work_Meetings"].append(item)
            else:
                categorized["Work_Projects"].append(item)  # Default
        
        return {
            "extracted_items": extracted_items,
            "categorized": categorized
        }
    
    @classmethod
    def _extract_relevant_snippet(cls, text: str, keywords: List[str]) -> str:
        """Extract a relevant snippet around keywords."""
        sentences = text.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            if any(kw in sentence.lower() for kw in keywords):
                relevant_sentences.append(sentence.strip())
                if len(relevant_sentences) >= 2:  # Get 2 sentences max
                    break
        
        return '. '.join(relevant_sentences) if relevant_sentences else text[:200]

