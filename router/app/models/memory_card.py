"""
Pydantic models for Memory Cards and Context Packs.
"""
from pydantic import BaseModel, Field
from typing import Literal, List
from datetime import datetime
import uuid


class MemoryCard(BaseModel):
    """An atomic memory card stored in the Context Wallet."""
    
    id: str = Field(default_factory=lambda: f"card_{uuid.uuid4().hex[:8]}")
    type: Literal["constraint", "preference", "goal", "capability"] = Field(..., description="Type of memory card")
    domain: List[str] = Field(default_factory=list, description="Domains this applies to (food, shopping, coding, etc.)")
    priority: Literal["hard", "soft"] = Field(default="soft", description="Hard constraints override preferences")
    text: str = Field(..., description="The actual constraint/preference/goal text")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    persona: str = Field(default="Personal", description="Persona this belongs to (Work/Personal/Travel)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class ContextPackRequest(BaseModel):
    """Request to generate a Context Pack for a draft prompt."""
    
    draft_prompt: str = Field(..., description="The user's draft prompt")
    site_id: str = Field(..., description="Which site (chatgpt, claude, gemini)")
    persona: str = Field(default="Personal", description="Which persona to use")
    sensitivity_mode: Literal["quiet", "normal", "verbose"] = Field(default="quiet", description="How much context to include")


class ContextPack(BaseModel):
    """The Context Pack returned to the extension."""
    
    pack_text: str = Field(..., description="Formatted context text to prepend to prompt")
    used_cards: List[str] = Field(default_factory=list, description="IDs of Memory Cards used")
    conflicts: List[dict] = Field(default_factory=list, description="Detected conflicts and resolutions")
    explain: List[str] = Field(default_factory=list, description="Human-readable explanations")


class ContextPackResponse(BaseModel):
    """Response containing the Context Pack."""
    
    success: bool
    pack: ContextPack
    message: str | None = None

