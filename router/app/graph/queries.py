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

