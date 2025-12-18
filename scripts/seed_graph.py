"""
Seed the Neo4j graph with demo data for the hackathon presentation.
"""
import asyncio
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add router to path for imports
ROOT_DIR = Path(__file__).parent.parent
ROUTER_DIR = ROOT_DIR / "router"
sys.path.insert(0, str(ROUTER_DIR))

from app.services.graph_service import GraphService
from app.models.tuples import SemanticTuple


DEMO_TUPLES = [
    # User preferences (established over time)
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="LIKES",
        object="Steakhouse X",
        object_type="Restaurant",
        confidence=0.9,
        source="historical",
        properties={"visits": 12, "last_visit": "2024-01-01"}
    ),
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="PREFERS",
        object="Premium Products",
        object_type="Shopping",
        confidence=0.8,
        source="historical",
        properties={"avg_spend": 150}
    ),
    
    # Recent constraints (override preferences)
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="HAS_CONSTRAINT",
        object="No Red Meat Diet",
        object_type="Diet",
        confidence=1.0,
        source="chat",
        properties={"started_days_ago": 3, "reason": "health"}
    ),
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="HAS_GOAL",
        object="Budget $50/month",
        object_type="Budget",
        confidence=0.95,
        source="chat",
        properties={"category": "supplements", "value": 50}
    ),
    
    # Food preferences
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="PREFERS",
        object="Vegan",
        object_type="Diet",
        confidence=0.7,
        source="browser",
        properties={"source": "Amazon searches"}
    ),
    
    # Alternative restaurants
    SemanticTuple(
        subject="User",
        subject_type="Person",
        predicate="LIKES",
        object="Sushi Place Y",
        object_type="Restaurant",
        confidence=0.7,
        source="historical",
        properties={"visits": 5, "cuisine": "Japanese"}
    ),
]


async def seed_demo_data():
    """Seed the graph with demo data."""
    print("🌱 Seeding demo data into Neo4j...")
    
    # Setup schema first
    await GraphService.setup_schema()
    
    # Ingest demo tuples
    for i, tuple_data in enumerate(DEMO_TUPLES):
        result = await GraphService.ingest_tuple(tuple_data, "demo_user")
        print(f"  [{i+1}/{len(DEMO_TUPLES)}] Ingested: ({tuple_data.subject})-[{tuple_data.predicate}]->({tuple_data.object})")
    
    print(f"\n✅ Seeded {len(DEMO_TUPLES)} tuples into the graph")
    
    # Close connection
    await GraphService.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())

