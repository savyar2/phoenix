"""
Phoenix Protocol - User Profile Models

Structured profile system with main profile, sub-profiles, and questions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any
from datetime import datetime
import uuid


class ProfileQuestion(BaseModel):
    """A question in a profile."""
    id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:8]}")
    question_text: str = Field(..., description="The question to ask")
    question_type: Literal["text", "multiple_choice", "scale", "boolean"] = Field(default="text")
    options: List[str] = Field(default_factory=list, description="Options for multiple choice")
    semantic_tags: List[str] = Field(default_factory=list, description="Semantic tags for cross-profile matching (e.g., 'options', 'price', 'quality')")
    required: bool = Field(default=True)
    order: int = Field(default=0, description="Display order")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProfileAnswer(BaseModel):
    """An answer to a profile question."""
    question_id: str = Field(..., description="ID of the question being answered")
    answer_text: str = Field(..., description="The answer text")
    answer_data: Optional[Dict] = Field(default=None, description="Additional structured data")
    answered_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class SubProfile(BaseModel):
    """A sub-profile (shopping, eating, health, work, etc.) with nested categories."""
    id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Sub-profile name (e.g., 'Shopping', 'Eating', 'Health', 'Work')")
    description: Optional[str] = None
    icon: Optional[str] = None  # Icon identifier
    categories: List[str] = Field(default_factory=list, description="Nested categories (e.g., ['Finance', 'Coding', 'Projects'] for Work)")
    questions: List[ProfileQuestion] = Field(default_factory=list, description="5-10 questions for this sub-profile")
    answers: List[ProfileAnswer] = Field(default_factory=list, description="Answers to questions")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class UserProfile(BaseModel):
    """Main user profile with baseline context."""
    user_id: str = Field(..., description="User identifier")
    main_questions: List[ProfileQuestion] = Field(default_factory=list, description="12 baseline questions")
    main_answers: List[ProfileAnswer] = Field(default_factory=list, description="Answers to main questions")
    sub_profiles: List[SubProfile] = Field(default_factory=list, description="Sub-profiles (shopping, eating, health, work)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class ConversationExtractionRequest(BaseModel):
    """Request to extract information from a conversation."""
    conversation_id: str = Field(..., description="Identifier for the conversation")
    conversation_text: str = Field(..., description="Full conversation text")
    messages: List[Dict] = Field(default_factory=list, description="Structured messages")
    user_id: str = Field(..., description="User identifier")


class ConversationExtractionResponse(BaseModel):
    """Response from conversation extraction."""
    success: bool
    extracted_items: List[Dict] = Field(default_factory=list, description="Extracted information items")
    categorized: Dict[str, Any] = Field(default_factory=dict, description="Items categorized by sub-profile/category (can be nested)")
    memory_cards_created: int = Field(default=0, description="Number of memory cards created from extraction")
    message: str


class CreateProfileRequest(BaseModel):
    """Request to create or update a user profile."""
    user_id: str = Field(..., description="User identifier")


class UpdateAnswerRequest(BaseModel):
    """Request to update an answer to a question."""
    question_id: str = Field(..., description="Question ID")
    answer_text: str = Field(..., description="Answer text")
    answer_data: Optional[Dict] = None


class CreateSubProfileRequest(BaseModel):
    """Request to create a sub-profile."""
    name: str = Field(..., description="Sub-profile name")
    description: Optional[str] = None
    categories: List[str] = Field(default_factory=list)


class AddQuestionRequest(BaseModel):
    """Request to add a question to a profile."""
    sub_profile_id: Optional[str] = Field(None, description="Sub-profile ID (None for main profile)")
    question_text: str = Field(..., description="Question text")
    question_type: Literal["text", "multiple_choice", "scale", "boolean"] = Field(default="text")
    options: List[str] = Field(default_factory=list)
    required: bool = Field(default=True)
    order: int = Field(default=0)

