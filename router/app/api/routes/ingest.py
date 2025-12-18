"""
Phoenix Protocol - Ingestion API Routes

Endpoints for ingesting raw context and extracting tuples.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.distiller import Distiller
from app.services.graph_service import GraphService
from app.models.tuples import RawContextInput, SemanticTuple

router = APIRouter()


class DistillResponse(BaseModel):
    """Response from distillation."""
    success: bool
    tuples: list[SemanticTuple]
    ingested: bool
    message: str


@router.post("/distill", response_model=DistillResponse)
async def distill_context(input_data: RawContextInput):
    """
    Distill raw context into semantic tuples and optionally ingest.
    
    This is the main entry point for the "Life Logger" - it takes
    raw user behavior/statements and converts them to graph-ready tuples.
    """
    try:
        # Extract tuples using local LLM
        tuples = await Distiller.extract_tuples(
            input_data.context,
            source=input_data.source
        )
        
        if not tuples:
            return DistillResponse(
                success=True,
                tuples=[],
                ingested=False,
                message="No tuples could be extracted from the context"
            )
        
        # Ingest into graph
        for tuple_data in tuples:
            await GraphService.ingest_tuple(tuple_data, input_data.user_id)
        
        return DistillResponse(
            success=True,
            tuples=tuples,
            ingested=True,
            message=f"Extracted and ingested {len(tuples)} tuples"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def distiller_health():
    """Check availability of all LLM providers."""
    health = await Distiller.health_check()
    return {
        "status": "healthy" if any(health.values()) else "unhealthy",
        **health
    }

