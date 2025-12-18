"""
Phoenix Protocol - Data Models
"""
from app.models.tuples import (
    SemanticTuple,
    TupleIngestionRequest,
    TupleIngestionResponse,
    RawContextInput,
)

# Import agent models if they exist
try:
    from app.models.agent_state import CheckpointMetadata, AgentCheckpoint
    __all__ = [
        "SemanticTuple",
        "TupleIngestionRequest",
        "TupleIngestionResponse",
        "RawContextInput",
        "CheckpointMetadata",
        "AgentCheckpoint",
    ]
except ImportError:
    __all__ = [
        "SemanticTuple",
        "TupleIngestionRequest",
        "TupleIngestionResponse",
        "RawContextInput",
    ]
