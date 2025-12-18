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

