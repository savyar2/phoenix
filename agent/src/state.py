"""
Phoenix Agent - State Definition

This defines the agent's working memory structure.
The state is what gets checkpointed by MemVerge.
"""
from typing import Annotated, Sequence, TypedDict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime
from pydantic import BaseModel, Field


class UserContext(TypedDict):
    """Context loaded from Neo4j graph."""
    user_id: str
    preferences: list[dict]
    constraints: list[dict]
    goals: list[dict]
    recent_actions: list[dict]
    conflicts: list[dict]


class TaskStep(TypedDict):
    """A single step in a multi-step task."""
    step_number: int
    description: str
    status: str  # pending, in_progress, completed, failed
    result: Any
    started_at: datetime | None
    completed_at: datetime | None


class AgentState(TypedDict):
    """
    The complete state of the Phoenix Agent.
    
    This entire structure is what gets frozen by MemVerge.
    On restore, the agent resumes exactly where it left off.
    """
    # Message history (LangGraph standard)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # User identification
    user_id: str
    
    # User context from Neo4j
    user_context: UserContext | None
    
    # Current task information
    current_task: str | None
    task_steps: list[TaskStep]
    current_step_index: int
    total_steps: int
    
    # Execution tracking
    started_at: datetime | None
    last_checkpoint_at: datetime | None
    checkpoint_count: int
    
    # Decision state (for demos)
    pending_decision: dict | None
    conflict_detected: dict | None
    resolution_applied: dict | None
    
    # Final output
    final_response: str | None
    task_completed: bool


class CheckpointMetadata(BaseModel):
    """Metadata for a checkpoint (stored alongside MemVerge snapshot)."""
    checkpoint_id: str
    agent_state_hash: str
    step_number: int
    total_steps: int
    task_description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    memverge_snapshot_id: str | None = None

