"""
Phoenix Protocol - MemVerge API Routes

Endpoints for checkpoint/restore operations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.memverge_service import MemVergeService
from app.models.agent_state import CheckpointMetadata

router = APIRouter()


class CreateCheckpointRequest(BaseModel):
    """Request to create a checkpoint."""
    container_id: str = "phoenix-agent"
    step_number: int
    total_steps: int
    task_description: str


class RestoreRequest(BaseModel):
    """Request to restore from checkpoint."""
    checkpoint_id: Optional[str] = None  # None = latest


class CrashSimulationRequest(BaseModel):
    """Request to simulate a crash (demo only)."""
    container_id: str = "phoenix-agent"
    delay_seconds: float = 0.0


@router.post("/checkpoint")
async def create_checkpoint(request: CreateCheckpointRequest):
    """
    Create a checkpoint of the agent's current state.
    
    This is called automatically during agent execution,
    but can also be triggered manually.
    """
    try:
        metadata = await MemVergeService.create_checkpoint(
            container_id=request.container_id,
            step_number=request.step_number,
            total_steps=request.total_steps,
            task_description=request.task_description
        )
        
        return {
            "success": True,
            "checkpoint": metadata.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_from_checkpoint(request: RestoreRequest):
    """
    Restore the agent from a checkpoint.
    
    THIS IS THE KEY DEMO for MemVerge judges!
    Shows the agent waking up exactly where it left off.
    """
    try:
        result = await MemVergeService.restore_from_checkpoint(request.checkpoint_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkpoints")
async def list_checkpoints(limit: int = 10):
    """
    List available checkpoints.
    
    Returns checkpoints sorted by timestamp (newest first).
    """
    checkpoints = await MemVergeService.list_checkpoints(limit)
    return {
        "checkpoints": [c.model_dump() for c in checkpoints]
    }


@router.get("/checkpoint/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: str):
    """Get details of a specific checkpoint."""
    checkpoints = await MemVergeService.list_checkpoints(100)
    for ckpt in checkpoints:
        if ckpt.checkpoint_id == checkpoint_id:
            return {"checkpoint": ckpt.model_dump()}
    raise HTTPException(status_code=404, detail="Checkpoint not found")


@router.delete("/checkpoint/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """Delete a checkpoint."""
    deleted = await MemVergeService.delete_checkpoint(checkpoint_id)
    if deleted:
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Checkpoint not found")


@router.post("/simulate-crash")
async def simulate_crash(request: CrashSimulationRequest):
    """
    Simulate an agent crash for demo purposes.
    
    ⚠️ DEMO ONLY - This forcefully kills the agent container!
    """
    import asyncio
    
    if request.delay_seconds > 0:
        await asyncio.sleep(request.delay_seconds)
    
    result = await MemVergeService.simulate_crash(request.container_id)
    return result


@router.get("/demo-status")
async def get_demo_status():
    """
    Get the current status for demo purposes.
    
    Shows:
    - Number of checkpoints available
    - Last checkpoint time
    - Whether agent is crashed or running
    """
    checkpoints = await MemVergeService.list_checkpoints(1)
    
    return {
        "checkpoints_available": len(await MemVergeService.list_checkpoints(100)),
        "latest_checkpoint": checkpoints[0].model_dump() if checkpoints else None,
        "agent_status": "unknown",  # Would check actual container status
        "ready_for_demo": len(checkpoints) > 0
    }

