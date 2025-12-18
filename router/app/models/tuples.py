"""
Phoenix Protocol - Semantic Tuple Models

These models represent the structured knowledge that gets ingested into Neo4j.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class SemanticTuple(BaseModel):
    """A semantic tuple representing a relationship in the knowledge graph."""
    
    subject: str = Field(..., description="The entity performing or being described")
    subject_type: str = Field(default="Person", description="Type of subject (Person, Product, etc.)")
    predicate: str = Field(..., description="The relationship (PREFERS, HAS_GOAL, HAS_CONSTRAINT, etc.)")
    object: str = Field(..., description="The target entity")
    object_type: str = Field(default="Entity", description="Type of object (Diet, Budget, Restaurant, etc.)")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0.0 to 1.0")
    source: str = Field(default="manual", description="Source of this tuple (chat, browser, historical, etc.)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional key-value properties")


class TupleIngestionRequest(BaseModel):
    """Request to ingest semantic tuples into the graph."""
    
    user_id: str = Field(default="default_user", description="User ID for this ingestion")
    tuples: List[SemanticTuple] = Field(..., description="List of semantic tuples to ingest")


class TupleIngestionResponse(BaseModel):
    """Response from tuple ingestion."""
    
    success: bool
    ingested_count: int
    message: str


class RawContextInput(BaseModel):
    """Raw context input for distillation into tuples."""
    
    user_id: str = Field(default="default_user", description="User ID")
    context: str = Field(..., description="Raw context text to extract tuples from")
    source: str = Field(default="manual", description="Source of the context")

