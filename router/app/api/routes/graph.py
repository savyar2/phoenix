"""
Phoenix Protocol - Graph API Routes

Endpoints for Neo4j graph operations.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any

from app.services.graph_service import GraphService
from app.models.tuples import SemanticTuple, TupleIngestionRequest, TupleIngestionResponse

router = APIRouter()


class GraphQueryRequest(BaseModel):
    """Request for querying the graph."""
    user_id: str = "default_user"
    query_type: str = "context"  # context, conflicts, recommendations
    category: str | None = None


class ConflictResolutionRequest(BaseModel):
    """Request to resolve a specific conflict type."""
    user_id: str = "default_user"
    preference_type: str  # e.g., "Diet", "Budget", "Restaurant"


@router.post("/ingest", response_model=TupleIngestionResponse)
async def ingest_tuples(request: TupleIngestionRequest):
    """
    Ingest semantic tuples into the graph.
    
    This is how the "Life Logger" feeds data into the Soul.
    """
    try:
        ingested = 0
        for tuple_data in request.tuples:
            await GraphService.ingest_tuple(tuple_data, request.user_id)
            ingested += 1
        
        return TupleIngestionResponse(
            success=True,
            ingested_count=ingested,
            message=f"Successfully ingested {ingested} tuples into the graph"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{user_id}")
async def get_user_context(user_id: str):
    """
    Get the full context for a user.
    
    Returns preferences, constraints, goals, and potential conflicts.
    This is what the agent loads before making decisions.
    """
    try:
        context = await GraphService.query_user_context(user_id)
        return {"success": True, "context": context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve-conflict")
async def resolve_conflict(request: ConflictResolutionRequest):
    """
    Resolve a conflict between preference and constraint.
    
    THIS IS THE KEY DEMO for Neo4j judges!
    Shows how the graph decides between competing requirements.
    """
    try:
        resolution = await GraphService.resolve_conflict(
            request.user_id,
            request.preference_type
        )
        return {"success": True, "resolution": resolution}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualize/{user_id}")
async def get_visualization_data(user_id: str, limit: int = 50):
    """
    Get graph data formatted for frontend visualization.
    
    Returns nodes and edges in a format compatible with
    react-force-graph, neovis.js, or similar libraries.
    """
    try:
        viz_data = await GraphService.get_graph_visualization(user_id, limit)
        return {"success": True, "graph": viz_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-schema")
async def setup_schema():
    """Initialize the graph schema (run once)."""
    try:
        await GraphService.setup_schema()
        return {"success": True, "message": "Schema setup complete"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def graph_health():
    """Check Neo4j connection health."""
    try:
        driver = await GraphService.get_driver()
        await driver.verify_connectivity()
        return {"status": "healthy", "connected": True}
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "error": str(e)}

