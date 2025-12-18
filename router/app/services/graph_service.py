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
            
            # Determine node labels based on predicate and types
            # For User subject, create User node; otherwise Entity
            subject_label = "User" if tuple_data.subject_type == "Person" and tuple_data.subject == "User" else "Entity"
            
            # Determine object label based on predicate
            if tuple_data.predicate in ["PREFERS", "LIKES", "DISLIKES"]:
                object_label = "Preference"
            elif tuple_data.predicate == "HAS_CONSTRAINT":
                object_label = "Constraint"
            elif tuple_data.predicate == "HAS_GOAL":
                object_label = "Goal"
            else:
                object_label = "Entity"
            
            # Create relationship type from predicate
            rel_type = tuple_data.predicate
            
            # Create or merge nodes and relationship
            query = f"""
            MERGE (subject:{subject_label} {{id: $subject_id}})
            ON CREATE SET 
                subject.name = $subject_name,
                subject.type = $subject_type,
                subject.created_at = datetime()
            ON MATCH SET
                subject.updated_at = datetime()
            
            MERGE (object:{object_label} {{id: $object_id}})
            ON CREATE SET
                object.name = $object_name,
                object.type = $object_type,
                object.created_at = datetime()
            ON MATCH SET
                object.updated_at = datetime()
            
            MERGE (subject)-[r:{rel_type}]->(object)
            ON CREATE SET
                r.created_at = datetime(),
                r.confidence = $confidence,
                r.source = $source
            ON MATCH SET
                r.updated_at = datetime(),
                r.confidence = $confidence
            
            RETURN subject, r, object
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
            }
            
            # Add properties to params if they exist
            if tuple_data.properties:
                params.update(tuple_data.properties)
            
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
            // Find the user
            MATCH (user:User {id: $user_id})
            
            // Get preferences
            OPTIONAL MATCH (user)-[pref_rel]->(preference)
            WHERE type(pref_rel) IN ['PREFERS', 'LIKES', 'DISLIKES']
            
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
            MATCH (user:User {id: $user_id})-[likes:PREFERS|LIKES]->(preference)
            WHERE preference.type = $preference_type
            
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
                node_id = str(n.get('id', ''))
                if node_id and node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "label": n.get('name', node_id),
                        "type": list(n.labels)[0] if n.labels else 'Entity',
                        "properties": dict(n.items())
                    }
                
                # Process target node
                m = record['m']
                target_id = str(m.get('id', ''))
                if target_id and target_id not in nodes:
                    nodes[target_id] = {
                        "id": target_id,
                        "label": m.get('name', target_id),
                        "type": list(m.labels)[0] if m.labels else 'Entity',
                        "properties": dict(m.items())
                    }
                
                # Process relationship
                r = record['r']
                rel_type = str(r.type)
                edges.append({
                    "source": node_id,
                    "target": target_id,
                    "type": rel_type,
                    "properties": dict(r.items())
                })
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }

