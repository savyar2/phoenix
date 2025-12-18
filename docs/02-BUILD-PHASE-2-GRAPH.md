# 💎 Phase 2: Neo4j Graph Integration

**Estimated Time: 3-4 hours**

This phase implements the "Soul" of the Phoenix Protocol - the Neo4j graph that stores semantic relationships and enables conflict resolution.

---

## 2.1 Neo4j Setup

### Step 1: Create Neo4j AuraDB Instance

1. Go to [Neo4j Aura](https://neo4j.com/cloud/platform/aura-graph-database/)
2. Sign up for free tier
3. Create new database:
   - Name: `phoenix-memory`
   - Region: Choose closest to you
   - Type: Free (or Developer if available)
4. **Save the credentials** - you only see them once!
5. Update `.env` with:
   ```
   NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-generated-password
   ```

### Step 2: Define Graph Schema

Create `backend/app/graph/schema.py`:

```python
"""
Phoenix Protocol - Neo4j Graph Schema

This defines the semantic structure of the "Soul" - the long-term memory graph.

Node Types:
- User: The person being modeled
- Entity: Abstract entities (concepts, items, places)
- Preference: Things the user likes/prefers
- Constraint: Limitations, rules, goals
- Action: Things the user has done
- Context: Temporal/situational context

Relationship Types:
- PREFERS: User preferences (diet, style, etc.)
- HAS_GOAL: User goals (budget, health, etc.)
- HAS_CONSTRAINT: User constraints (restrictions)
- PERFORMED: Actions taken
- OVERRIDES: When one preference overrides another
- CONFLICTS_WITH: Detected conflicts
- RELATED_TO: General associations
"""

# Cypher query to create indexes and constraints
SCHEMA_SETUP_QUERIES = [
    # Constraints for unique identifiers
    "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT preference_id IF NOT EXISTS FOR (p:Preference) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT constraint_id IF NOT EXISTS FOR (c:Constraint) REQUIRE c.id IS UNIQUE",
    
    # Indexes for common queries
    "CREATE INDEX user_name IF NOT EXISTS FOR (u:User) ON (u.name)",
    "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
    "CREATE INDEX preference_category IF NOT EXISTS FOR (p:Preference) ON (p.category)",
    "CREATE INDEX constraint_category IF NOT EXISTS FOR (c:Constraint) ON (c.category)",
    
    # Full-text index for semantic search fallback
    """
    CREATE FULLTEXT INDEX entity_search IF NOT EXISTS 
    FOR (e:Entity) ON EACH [e.name, e.description]
    """
]


# Node label definitions
NODE_LABELS = {
    "User": ["id", "name", "created_at"],
    "Entity": ["id", "name", "type", "description", "created_at"],
    "Preference": ["id", "name", "category", "value", "strength", "created_at", "expires_at"],
    "Constraint": ["id", "name", "category", "value", "priority", "created_at", "expires_at"],
    "Action": ["id", "description", "timestamp", "outcome"],
    "Context": ["id", "type", "value", "active_from", "active_to"],
}


# Relationship type definitions
RELATIONSHIP_TYPES = {
    "PREFERS": ["strength", "since", "context"],
    "HAS_GOAL": ["target_value", "deadline", "priority"],
    "HAS_CONSTRAINT": ["reason", "priority", "active"],
    "PERFORMED": ["timestamp", "outcome", "confidence"],
    "OVERRIDES": ["reason", "since", "confidence"],
    "CONFLICTS_WITH": ["detected_at", "resolution"],
    "RELATED_TO": ["type", "strength"],
}
```

### Step 3: Create Graph Service

Create `backend/app/services/graph_service.py`:

```python
"""
Phoenix Protocol - Neo4j Graph Service

Handles all interactions with the Neo4j graph database.
"""
import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver
from contextlib import asynccontextmanager
from typing import Any
from datetime import datetime
import uuid

from app.config import get_settings
from app.models.tuples import SemanticTuple
from app.graph.schema import SCHEMA_SETUP_QUERIES

logger = structlog.get_logger()
settings = get_settings()


class GraphService:
    """Service for Neo4j graph operations."""
    
    _driver: AsyncDriver | None = None
    
    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        """Get or create the Neo4j driver."""
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # Verify connectivity
            await cls._driver.verify_connectivity()
            logger.info("Neo4j connection established")
        return cls._driver
    
    @classmethod
    async def close(cls):
        """Close the Neo4j driver."""
        if cls._driver:
            await cls._driver.close()
            cls._driver = None
            logger.info("Neo4j connection closed")
    
    @classmethod
    @asynccontextmanager
    async def session(cls):
        """Context manager for Neo4j sessions."""
        driver = await cls.get_driver()
        async with driver.session() as session:
            yield session
    
    @classmethod
    async def setup_schema(cls):
        """Initialize the graph schema."""
        async with cls.session() as session:
            for query in SCHEMA_SETUP_QUERIES:
                try:
                    await session.run(query)
                    logger.debug(f"Executed schema query: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Schema query failed (may already exist): {e}")
        logger.info("Graph schema setup complete")
    
    @classmethod
    async def ingest_tuple(cls, tuple_data: SemanticTuple, user_id: str = "default_user") -> dict:
        """
        Ingest a semantic tuple into the graph.
        
        Creates nodes and relationships based on the tuple structure.
        """
        async with cls.session() as session:
            # Generate IDs
            subject_id = f"{user_id}_{tuple_data.subject}_{tuple_data.subject_type}".lower().replace(" ", "_")
            object_id = f"{tuple_data.object}_{tuple_data.object_type}".lower().replace(" ", "_")
            
            # Create or merge nodes and relationship
            query = """
            MERGE (subject:Entity {id: $subject_id})
            ON CREATE SET 
                subject.name = $subject_name,
                subject.type = $subject_type,
                subject.created_at = datetime()
            ON MATCH SET
                subject.updated_at = datetime()
            
            MERGE (object:Entity {id: $object_id})
            ON CREATE SET
                object.name = $object_name,
                object.type = $object_type,
                object.created_at = datetime()
            ON MATCH SET
                object.updated_at = datetime()
            
            MERGE (subject)-[r:RELATES_TO {type: $predicate}]->(object)
            ON CREATE SET
                r.created_at = datetime(),
                r.confidence = $confidence,
                r.source = $source
            ON MATCH SET
                r.updated_at = datetime(),
                r.confidence = $confidence
            
            RETURN subject, r, object
            """
            
            # Also create a more specific relationship based on predicate
            specific_query = """
            MATCH (subject:Entity {id: $subject_id})
            MATCH (object:Entity {id: $object_id})
            
            CALL apoc.merge.relationship(
                subject, 
                $predicate, 
                {created_at: datetime(), confidence: $confidence, source: $source},
                {updated_at: datetime()},
                object,
                {}
            ) YIELD rel
            
            RETURN rel
            """
            
            params = {
                "subject_id": subject_id,
                "subject_name": tuple_data.subject,
                "subject_type": tuple_data.subject_type,
                "object_id": object_id,
                "object_name": tuple_data.object,
                "object_type": tuple_data.object_type,
                "predicate": tuple_data.predicate,
                "confidence": tuple_data.confidence,
                "source": tuple_data.source,
                "properties": tuple_data.properties
            }
            
            result = await session.run(query, params)
            record = await result.single()
            
            logger.info(f"Ingested tuple: ({tuple_data.subject})-[{tuple_data.predicate}]->({tuple_data.object})")
            
            return {
                "success": True,
                "subject_id": subject_id,
                "object_id": object_id,
                "relationship": tuple_data.predicate
            }
    
    @classmethod
    async def query_user_context(cls, user_id: str, query_text: str = "") -> dict:
        """
        Get the full context for a user to inform agent decisions.
        
        This is the key GraphRAG query that retrieves:
        - User preferences
        - Active constraints/goals
        - Recent actions
        - Potential conflicts
        """
        async with cls.session() as session:
            query = """
            // Find the user's preferences
            MATCH (user:Entity {type: 'User'})-[pref_rel]->(preference)
            WHERE user.id CONTAINS $user_id
            
            // Collect preferences
            WITH user, collect({
                type: type(pref_rel),
                target: preference.name,
                category: preference.type,
                confidence: pref_rel.confidence,
                created: pref_rel.created_at
            }) as preferences
            
            // Find constraints
            OPTIONAL MATCH (user)-[const_rel:HAS_GOAL|HAS_CONSTRAINT]->(constraint)
            WITH user, preferences, collect({
                type: type(const_rel),
                name: constraint.name,
                value: constraint.value,
                priority: const_rel.priority
            }) as constraints
            
            // Find potential conflicts
            OPTIONAL MATCH (pref1)<-[]-(user)-[]->(pref2)
            WHERE pref1.type = pref2.type AND pref1 <> pref2
            WITH user, preferences, constraints, collect({
                item1: pref1.name,
                item2: pref2.name,
                conflict_type: pref1.type
            }) as potential_conflicts
            
            RETURN {
                user_id: user.id,
                preferences: preferences,
                constraints: constraints,
                potential_conflicts: potential_conflicts
            } as context
            """
            
            result = await session.run(query, {"user_id": user_id})
            records = await result.data()
            
            if records:
                return records[0].get("context", {})
            return {"preferences": [], "constraints": [], "potential_conflicts": []}
    
    @classmethod
    async def resolve_conflict(cls, user_id: str, preference_type: str) -> dict:
        """
        Resolve conflicts between preferences using graph logic.
        
        This is THE KEY DEMO for Neo4j judges:
        Shows how the graph resolves "I like X but my constraint says Y"
        """
        async with cls.session() as session:
            query = """
            // Find conflicting preferences and constraints
            MATCH (user:Entity {type: 'User'})-[likes:PREFERS|LIKES]->(preference)
            WHERE user.id CONTAINS $user_id
            AND preference.type = $preference_type
            
            OPTIONAL MATCH (user)-[constraint:HAS_GOAL|HAS_CONSTRAINT]->(goal)
            WHERE goal.type = $preference_type OR goal.category = $preference_type
            
            // Determine winner based on priority and recency
            WITH user, preference, likes, goal, constraint,
                 CASE 
                     WHEN constraint IS NOT NULL AND constraint.priority > coalesce(likes.strength, 0.5)
                     THEN 'constraint_wins'
                     WHEN constraint IS NOT NULL 
                     THEN 'preference_wins_but_warn'
                     ELSE 'preference_wins'
                 END as resolution
            
            RETURN {
                preference: preference.name,
                preference_strength: likes.strength,
                constraint: goal.name,
                constraint_priority: constraint.priority,
                resolution: resolution,
                reasoning: CASE resolution
                    WHEN 'constraint_wins' 
                    THEN 'Your recent ' + goal.name + ' overrides your usual preference for ' + preference.name
                    WHEN 'preference_wins_but_warn'
                    THEN 'Going with ' + preference.name + ' but note: you have a goal of ' + goal.name
                    ELSE 'No conflicts detected, proceeding with ' + preference.name
                END
            } as result
            """
            
            result = await session.run(query, {
                "user_id": user_id,
                "preference_type": preference_type
            })
            records = await result.data()
            
            if records:
                return records[0].get("result", {})
            return {"resolution": "no_data", "reasoning": "No preferences found for this type"}
    
    @classmethod
    async def get_graph_visualization(cls, user_id: str, limit: int = 50) -> dict:
        """Get graph data formatted for frontend visualization."""
        async with cls.session() as session:
            query = """
            MATCH (n)-[r]->(m)
            WHERE n.id CONTAINS $user_id OR m.id CONTAINS $user_id
            RETURN n, r, m
            LIMIT $limit
            """
            
            result = await session.run(query, {"user_id": user_id, "limit": limit})
            records = await result.data()
            
            nodes = {}
            edges = []
            
            for record in records:
                # Process source node
                n = record['n']
                if n['id'] not in nodes:
                    nodes[n['id']] = {
                        "id": n['id'],
                        "label": n.get('name', n['id']),
                        "type": n.get('type', 'Entity'),
                        "properties": dict(n)
                    }
                
                # Process target node
                m = record['m']
                if m['id'] not in nodes:
                    nodes[m['id']] = {
                        "id": m['id'],
                        "label": m.get('name', m['id']),
                        "type": m.get('type', 'Entity'),
                        "properties": dict(m)
                    }
                
                # Process relationship
                r = record['r']
                edges.append({
                    "source": n['id'],
                    "target": m['id'],
                    "type": type(r).__name__ if hasattr(r, '__name__') else str(r.type),
                    "properties": dict(r) if hasattr(r, 'items') else {}
                })
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }
```

---

## 2.2 Cypher Query Templates

Create `backend/app/graph/queries.py`:

```python
"""
Phoenix Protocol - Cypher Query Templates

These are the key queries that power the GraphRAG system.
"""

# ============================================
# INGESTION QUERIES
# ============================================

CREATE_USER = """
MERGE (u:User {id: $user_id})
ON CREATE SET u.name = $name, u.created_at = datetime()
RETURN u
"""

CREATE_PREFERENCE = """
MATCH (u:User {id: $user_id})
MERGE (p:Preference {id: $pref_id})
ON CREATE SET 
    p.name = $name,
    p.category = $category,
    p.value = $value,
    p.created_at = datetime()
MERGE (u)-[r:PREFERS]->(p)
ON CREATE SET r.strength = $strength, r.since = datetime()
ON MATCH SET r.strength = $strength, r.updated_at = datetime()
RETURN u, r, p
"""

CREATE_CONSTRAINT = """
MATCH (u:User {id: $user_id})
MERGE (c:Constraint {id: $constraint_id})
ON CREATE SET
    c.name = $name,
    c.category = $category,
    c.value = $value,
    c.created_at = datetime()
MERGE (u)-[r:HAS_CONSTRAINT]->(c)
ON CREATE SET r.priority = $priority, r.reason = $reason, r.since = datetime()
ON MATCH SET r.priority = $priority, r.updated_at = datetime()
RETURN u, r, c
"""

CREATE_GOAL = """
MATCH (u:User {id: $user_id})
MERGE (g:Goal {id: $goal_id})
ON CREATE SET
    g.name = $name,
    g.target_value = $target_value,
    g.deadline = $deadline,
    g.created_at = datetime()
MERGE (u)-[r:HAS_GOAL]->(g)
ON CREATE SET r.priority = $priority, r.since = datetime()
RETURN u, r, g
"""


# ============================================
# RETRIEVAL QUERIES (GraphRAG)
# ============================================

GET_USER_FULL_CONTEXT = """
// Get comprehensive user context for agent reasoning
MATCH (u:User {id: $user_id})

// Get all preferences
OPTIONAL MATCH (u)-[pref_rel:PREFERS]->(pref:Preference)
WITH u, collect({
    name: pref.name,
    category: pref.category,
    value: pref.value,
    strength: pref_rel.strength,
    since: pref_rel.since
}) as preferences

// Get all constraints
OPTIONAL MATCH (u)-[const_rel:HAS_CONSTRAINT]->(const:Constraint)
WITH u, preferences, collect({
    name: const.name,
    category: const.category,
    value: const.value,
    priority: const_rel.priority,
    reason: const_rel.reason
}) as constraints

// Get all goals
OPTIONAL MATCH (u)-[goal_rel:HAS_GOAL]->(goal:Goal)
WITH u, preferences, constraints, collect({
    name: goal.name,
    target: goal.target_value,
    deadline: goal.deadline,
    priority: goal_rel.priority
}) as goals

// Get recent actions
OPTIONAL MATCH (u)-[action_rel:PERFORMED]->(action:Action)
WHERE action.timestamp > datetime() - duration('P7D')  // Last 7 days
WITH u, preferences, constraints, goals, collect({
    description: action.description,
    timestamp: action.timestamp,
    outcome: action.outcome
}) as recent_actions

RETURN {
    user_id: u.id,
    user_name: u.name,
    preferences: preferences,
    constraints: constraints,
    goals: goals,
    recent_actions: recent_actions
} as context
"""


CONFLICT_DETECTION_QUERY = """
// Detect conflicts between preferences and constraints
MATCH (u:User {id: $user_id})

// Find preferences
MATCH (u)-[pref_rel:PREFERS]->(pref:Preference)

// Find constraints in the same category
MATCH (u)-[const_rel:HAS_CONSTRAINT]->(const:Constraint)
WHERE const.category = pref.category

// Detect if they conflict
WITH u, pref, pref_rel, const, const_rel,
     CASE 
         // Budget conflict: preference costs more than constraint allows
         WHEN const.category = 'Budget' AND toFloat(pref.value) > toFloat(const.value)
         THEN true
         // Diet conflict: preference violates diet constraint
         WHEN const.category = 'Diet' AND pref.category = 'Food'
         THEN true
         ELSE false
     END as has_conflict

WHERE has_conflict = true

RETURN {
    conflict_type: const.category,
    preference: {
        name: pref.name,
        value: pref.value,
        strength: pref_rel.strength
    },
    constraint: {
        name: const.name,
        value: const.value,
        priority: const_rel.priority
    },
    resolution: CASE
        WHEN const_rel.priority > pref_rel.strength THEN 'CONSTRAINT_WINS'
        ELSE 'PREFERENCE_WINS_WITH_WARNING'
    END
} as conflict
"""


SMART_RECOMMENDATION_QUERY = """
// Get recommendation that respects both preferences and constraints
MATCH (u:User {id: $user_id})

// Get relevant preferences for the query type
MATCH (u)-[pref_rel:PREFERS]->(pref:Preference)
WHERE pref.category = $query_category

// Get constraints that might apply
OPTIONAL MATCH (u)-[const_rel:HAS_CONSTRAINT]->(const:Constraint)
WHERE const.category IN [$query_category, 'Budget', 'Health', 'Diet']

// Calculate what's allowed
WITH u, pref, pref_rel, const, const_rel,
     CASE 
         WHEN const IS NULL THEN true
         WHEN const.category = 'Budget' AND toFloat(pref.value) <= toFloat(const.value) THEN true
         WHEN const.category = 'Diet' AND NOT pref.name CONTAINS const.value THEN true
         ELSE false
     END as is_allowed

WHERE is_allowed = true

RETURN {
    recommended: pref.name,
    category: pref.category,
    reason: 'Matches your preference' + 
            CASE WHEN const IS NOT NULL 
                 THEN ' and respects your ' + const.name 
                 ELSE '' 
            END,
    confidence: pref_rel.strength,
    constraints_respected: collect(DISTINCT const.name)
} as recommendation
ORDER BY pref_rel.strength DESC
LIMIT 1
"""


# ============================================
# DEMO-SPECIFIC QUERIES
# ============================================

DINNER_CONFLICT_DEMO = """
// Demo: Steakhouse vs No Red Meat conflict
MATCH (u:User {id: $user_id})

// User's usual restaurant preference
OPTIONAL MATCH (u)-[likes:LIKES|PREFERS]->(restaurant:Entity)
WHERE restaurant.type = 'Restaurant'

// User's diet constraint
OPTIONAL MATCH (u)-[diet:HAS_CONSTRAINT]->(diet_rule:Constraint)
WHERE diet_rule.category = 'Diet'

WITH u, restaurant, likes, diet_rule, diet,
     CASE
         WHEN diet_rule IS NOT NULL 
              AND restaurant.name CONTAINS 'Steak' 
              AND diet_rule.value CONTAINS 'No Red Meat'
         THEN {
             conflict: true,
             blocked: restaurant.name,
             reason: 'Your ' + diet_rule.name + ' diet started ' + 
                     toString(date(diet.since)) + ' blocks this choice',
             alternative_needed: true
         }
         ELSE {
             conflict: false,
             choice: restaurant.name,
             reason: 'No dietary conflicts'
         }
     END as result

RETURN result
"""
```

---

## 2.3 API Routes for Graph

Create `backend/app/api/routes/graph.py`:

```python
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
```

---

## 2.4 Local LLM Distiller

Create `backend/app/services/distiller.py`:

```python
"""
Phoenix Protocol - Local LLM Distiller

Uses Ollama/Llama to extract semantic tuples from raw user context.
This runs locally for privacy - no user data leaves the machine.
"""
import structlog
import json
from typing import List
import ollama

from app.config import get_settings
from app.models.tuples import SemanticTuple

logger = structlog.get_logger()
settings = get_settings()


EXTRACTION_PROMPT = """You are a semantic tuple extractor. Given user behavior or statements, extract structured relationships.

Output ONLY valid JSON array of tuples. Each tuple has:
- subject: The entity performing or being described (usually "User")
- subject_type: Type of subject (Person, Product, etc.)
- predicate: The relationship (PREFERS, HAS_GOAL, HAS_CONSTRAINT, LIKES, DISLIKES, WANTS, AVOIDS)
- object: The target entity
- object_type: Type of object (Diet, Budget, Restaurant, Food, Product, etc.)
- confidence: 0.0 to 1.0 based on how certain the statement is
- properties: Additional key-value properties if relevant

Examples:

Input: "I'm trying to stay under $50 this month for protein powder"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "HAS_GOAL", "object": "Budget $50", "object_type": "Budget", "confidence": 0.9, "properties": {"category": "Supplements", "timeframe": "monthly", "value": 50}}]

Input: "I started a vegan diet 3 days ago"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "HAS_CONSTRAINT", "object": "Vegan Diet", "object_type": "Diet", "confidence": 1.0, "properties": {"started_days_ago": 3, "restriction": "no animal products"}}]

Input: "User browsed Steakhouse X on Yelp"
Output: [{"subject": "User", "subject_type": "Person", "predicate": "INTERESTED_IN", "object": "Steakhouse X", "object_type": "Restaurant", "confidence": 0.6, "properties": {"cuisine": "Steakhouse", "source": "Yelp"}}]

Now extract tuples from:
Input: "{context}"

Output ONLY the JSON array, no other text:"""


class Distiller:
    """Extracts semantic tuples from raw context using local LLM."""
    
    @staticmethod
    async def extract_tuples(raw_context: str, source: str = "manual") -> List[SemanticTuple]:
        """
        Extract semantic tuples from raw context.
        
        Uses local Ollama for privacy-preserving extraction.
        """
        try:
            # Call Ollama
            response = ollama.chat(
                model=settings.ollama_model,
                messages=[{
                    'role': 'user',
                    'content': EXTRACTION_PROMPT.format(context=raw_context)
                }],
                options={
                    'temperature': 0.1,  # Low temperature for consistent extraction
                }
            )
            
            # Parse response
            content = response['message']['content'].strip()
            
            # Try to extract JSON from response
            # Handle potential markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            tuples_data = json.loads(content)
            
            # Convert to SemanticTuple objects
            tuples = []
            for t in tuples_data:
                tuples.append(SemanticTuple(
                    subject=t.get('subject', 'User'),
                    subject_type=t.get('subject_type', 'Person'),
                    predicate=t.get('predicate', 'RELATES_TO'),
                    object=t.get('object', ''),
                    object_type=t.get('object_type', 'Entity'),
                    confidence=t.get('confidence', 0.5),
                    source=source,
                    properties=t.get('properties', {})
                ))
            
            logger.info(f"Extracted {len(tuples)} tuples from context")
            return tuples
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Tuple extraction failed: {e}")
            return []
    
    @staticmethod
    async def health_check() -> bool:
        """Check if Ollama is running and model is available."""
        try:
            ollama.list()
            return True
        except Exception:
            return False
```

---

## 2.5 Ingestion API Route

Create `backend/app/api/routes/ingest.py`:

```python
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
    """Check if the distiller (Ollama) is available."""
    is_healthy = await Distiller.health_check()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "ollama_available": is_healthy
    }
```

---

## 2.6 Update Main App to Include Routes

Update `backend/app/main.py` to include the new routes:

```python
# Add these imports at the top
from app.api.routes import ingest, graph
from app.services.graph_service import GraphService

# In the lifespan function, add:
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🔥 Phoenix Protocol starting up...")
    
    # Initialize Neo4j
    try:
        await GraphService.get_driver()
        await GraphService.setup_schema()
        logger.info("✅ Neo4j connection established")
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🔥 Phoenix Protocol shutting down...")
    await GraphService.close()

# After app definition, add routers:
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingestion"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
```

---

## 2.7 Seed Script for Demo Data

Create `scripts/seed_graph.py`:

```python
"""
Seed the Neo4j graph with demo data for the hackathon presentation.
"""
import asyncio
from datetime import datetime, timedelta

# Add parent to path for imports
import sys
sys.path.insert(0, 'backend')

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
```

---

## 2.8 Phase 2 Verification

### Test 1: Neo4j Connection
```bash
cd backend
source venv/bin/activate
python -c "
import asyncio
from app.services.graph_service import GraphService

async def test():
    driver = await GraphService.get_driver()
    print('✅ Neo4j connected!')
    await GraphService.close()

asyncio.run(test())
"
```

### Test 2: Schema Setup
```bash
curl -X POST http://localhost:8000/api/graph/setup-schema
```

### Test 3: Ingest a Tuple
```bash
curl -X POST http://localhost:8000/api/graph/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "tuples": [{
      "subject": "User",
      "subject_type": "Person",
      "predicate": "PREFERS",
      "object": "Vegan Food",
      "object_type": "Diet",
      "confidence": 0.9
    }]
  }'
```

### Test 4: Query Context
```bash
curl http://localhost:8000/api/graph/context/test_user
```

### Test 5: Seed Demo Data
```bash
cd ..
python scripts/seed_graph.py
```

---

## 2.9 Phase 2 Deliverables Checklist

- [ ] Neo4j AuraDB instance created and configured
- [ ] Graph schema defined and applied
- [ ] GraphService with CRUD operations
- [ ] Cypher query templates for GraphRAG
- [ ] Conflict resolution logic implemented
- [ ] Local LLM distiller (Ollama) integration
- [ ] API routes for ingestion and querying
- [ ] Demo data seeded
- [ ] Graph visualization endpoint ready

---

## Next: [Phase 3 - LangGraph Agent](./03-BUILD-PHASE-3-AGENT.md)

