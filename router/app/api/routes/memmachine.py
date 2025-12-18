"""
Phoenix Protocol - MemMachine API Routes

Endpoints for interacting with MemMachine persistent memory layer.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.services.memmachine_service import MemMachineService

router = APIRouter()


class StoreMemoryRequest(BaseModel):
    """Request to store a memory in MemMachine."""
    user_id: str = Field(..., description="Unique identifier for the user")
    memory_type: str = Field(default="episodic", description="Type of memory (episodic, profile, etc.)")
    content: str = Field(..., description="The memory content to store")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")


class StoreMemoryResponse(BaseModel):
    """Response from storing a memory."""
    success: bool
    memory_id: Optional[str] = None
    message: str


class RecallMemoriesRequest(BaseModel):
    """Request to recall memories from MemMachine."""
    user_id: str = Field(..., description="Unique identifier for the user")
    query: str = Field(..., description="Query to search for relevant memories")
    memory_type: Optional[str] = Field(default=None, description="Optional filter by memory type")
    limit: int = Field(default=10, description="Maximum number of memories to return")


class RecallMemoriesResponse(BaseModel):
    """Response from recalling memories."""
    success: bool
    memories: List[Dict[str, Any]]
    count: int
    message: str


class UpdateProfileRequest(BaseModel):
    """Request to update user profile in MemMachine."""
    user_id: str = Field(..., description="Unique identifier for the user")
    profile_data: Dict[str, Any] = Field(..., description="Profile data to update")


class UpdateProfileResponse(BaseModel):
    """Response from updating profile."""
    success: bool
    message: str


class GetProfileResponse(BaseModel):
    """Response with user profile."""
    success: bool
    profile: Optional[Dict[str, Any]] = None
    message: str


@router.post("/store", response_model=StoreMemoryResponse)
async def store_memory(request: StoreMemoryRequest):
    """
    Store a memory in MemMachine.
    
    This allows the system to learn and remember information across sessions.
    """
    try:
        memory_id = await MemMachineService.store_memory(
            user_id=request.user_id,
            memory_type=request.memory_type,
            content=request.content,
            metadata=request.metadata
        )
        
        if memory_id:
            return StoreMemoryResponse(
                success=True,
                memory_id=memory_id,
                message="Memory stored successfully in MemMachine"
            )
        else:
            return StoreMemoryResponse(
                success=False,
                message="Failed to store memory. MemMachine may not be available."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recall", response_model=RecallMemoriesResponse)
async def recall_memories(request: RecallMemoriesRequest):
    """
    Recall relevant memories from MemMachine based on a query.
    
    This enables the system to retrieve context from past sessions.
    """
    try:
        memories = await MemMachineService.recall_memories(
            user_id=request.user_id,
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit
        )
        
        return RecallMemoriesResponse(
            success=True,
            memories=memories,
            count=len(memories),
            message=f"Retrieved {len(memories)} memories from MemMachine"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profile/update", response_model=UpdateProfileResponse)
async def update_profile(request: UpdateProfileRequest):
    """
    Update user profile in MemMachine.
    
    This allows the system to maintain a persistent user profile.
    """
    try:
        success = await MemMachineService.update_user_profile(
            user_id=request.user_id,
            profile_data=request.profile_data
        )
        
        if success:
            return UpdateProfileResponse(
                success=True,
                message="User profile updated successfully in MemMachine"
            )
        else:
            return UpdateProfileResponse(
                success=False,
                message="Failed to update profile. MemMachine may not be available."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}", response_model=GetProfileResponse)
async def get_profile(user_id: str):
    """
    Get user profile from MemMachine.
    
    Retrieve the persistent profile for a user.
    """
    try:
        profile = await MemMachineService.get_user_profile(user_id=user_id)
        
        if profile:
            return GetProfileResponse(
                success=True,
                profile=profile,
                message="Profile retrieved successfully"
            )
        else:
            return GetProfileResponse(
                success=False,
                profile=None,
                message="Profile not found or MemMachine not available"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def memmachine_health():
    """
    Check MemMachine service health and status.
    
    Returns the health status of the MemMachine connection.
    """
    try:
        health = await MemMachineService.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

