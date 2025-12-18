"""
Phoenix Protocol - Memory Card API Routes

Endpoints for creating and managing Memory Cards directly (without distiller).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

from app.models.memory_card import MemoryCard
from wallet.store.wallet_store import WalletStore
from app.config import get_settings

router = APIRouter()
settings = get_settings()

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


class CreateMemoryCardRequest(BaseModel):
    """Request to create a memory card manually."""
    type: Literal["constraint", "preference", "goal", "capability"] = Field(..., description="Type of memory card")
    text: str = Field(..., description="The actual constraint/preference/goal text")
    domain: List[str] = Field(default_factory=list, description="Domains this applies to (food, shopping, coding, etc.)")
    priority: Literal["hard", "soft"] = Field(default="soft", description="Hard constraints override preferences")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    persona: str = Field(default="Personal", description="Persona this belongs to (Work/Personal/Travel)")


class MemoryCardResponse(BaseModel):
    """Response with created memory card."""
    success: bool
    card: MemoryCard
    message: str


class ListMemoryCardsResponse(BaseModel):
    """Response with list of memory cards."""
    success: bool
    cards: List[MemoryCard]
    count: int


@router.post("/create", response_model=MemoryCardResponse)
async def create_memory_card(request: CreateMemoryCardRequest):
    """
    Create a memory card manually without using the distiller.
    
    This allows users to add context even when LLM providers are unavailable.
    """
    try:
        wallet = get_wallet_store()
        
        # Create MemoryCard object
        card = MemoryCard(
            type=request.type,
            text=request.text,
            domain=request.domain,
            priority=request.priority,
            tags=request.tags,
            persona=request.persona
        )
        
        # Save to wallet
        saved_card = wallet.add_card(card)
        
        return MemoryCardResponse(
            success=True,
            card=saved_card,
            message=f"Memory card '{saved_card.id}' created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ListMemoryCardsResponse)
async def list_memory_cards(
    persona: str = "Personal",
    domain: Optional[str] = None
):
    """
    List memory cards for a given persona and optional domain.
    """
    try:
        wallet = get_wallet_store()
        cards = wallet.get_cards(persona=persona, domain=domain)
        
        return ListMemoryCardsResponse(
            success=True,
            cards=cards,
            count=len(cards)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{card_id}")
async def get_memory_card(card_id: str):
    """Get a specific memory card by ID."""
    try:
        wallet = get_wallet_store()
        card = wallet.get_card(card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail=f"Memory card '{card_id}' not found")
        
        return {
            "success": True,
            "card": card
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{card_id}")
async def delete_memory_card(card_id: str):
    """Delete a memory card by ID."""
    try:
        wallet = get_wallet_store()
        deleted = wallet.delete_card(card_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Memory card '{card_id}' not found")
        
        return {
            "success": True,
            "message": f"Memory card '{card_id}' deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

