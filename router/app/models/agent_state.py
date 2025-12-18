"""
Phoenix Protocol - Agent State Models

Models for tracking agent state and checkpoints.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CheckpointMetadata(BaseModel):
    """Metadata for a checkpoint (stored alongside MemVerge snapshot)."""
    checkpoint_id: str
    agent_state_hash: str
    step_number: int
    total_steps: int
    task_description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    memverge_snapshot_id: Optional[str] = None


class AgentCheckpoint(BaseModel):
    """Complete checkpoint information including metadata."""
    metadata: CheckpointMetadata
    container_id: str
    restored: bool = False
    restored_at: Optional[datetime] = None

