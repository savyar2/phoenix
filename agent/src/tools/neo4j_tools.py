"""
Phoenix Agent - Neo4j Tools

Tools for the agent to query and update the graph.
"""
from langchain_core.tools import tool
from typing import Any
import httpx
import os

# Base URL for the Phoenix API
# Defaults to localhost for local dev, but can be overridden for Docker
API_BASE = os.getenv("PHOENIX_API_BASE", "http://localhost:8787")


@tool
def load_user_context(user_id: str) -> dict:
    """
    Load the full context for a user from the Neo4j graph.
    
    This retrieves:
    - User preferences (what they like)
    - Constraints (rules they've set)
    - Goals (what they're trying to achieve)
    - Recent actions
    - Potential conflicts
    
    Use this at the start of every task to understand the user.
    """
    try:
        response = httpx.get(f"{API_BASE}/api/graph/context/{user_id}")
        response.raise_for_status()
        return response.json().get("context", {})
    except Exception as e:
        return {"error": str(e), "preferences": [], "constraints": [], "goals": []}


@tool
def check_for_conflicts(user_id: str, decision_type: str) -> dict:
    """
    Check if there are conflicts between user preferences and constraints.
    
    Args:
        user_id: The user to check
        decision_type: The type of decision (e.g., "Restaurant", "Budget", "Diet")
    
    Returns:
        Conflict information and recommended resolution
    """
    try:
        response = httpx.post(
            f"{API_BASE}/api/graph/resolve-conflict",
            json={"user_id": user_id, "preference_type": decision_type}
        )
        response.raise_for_status()
        return response.json().get("resolution", {})
    except Exception as e:
        return {"error": str(e), "resolution": "unknown"}


@tool
def record_action(user_id: str, action_description: str, outcome: str) -> dict:
    """
    Record an action taken by/for the user in the graph.
    
    This creates a historical record that can influence future decisions.
    """
    try:
        response = httpx.post(
            f"{API_BASE}/api/graph/ingest",
            json={
                "user_id": user_id,
                "tuples": [{
                    "subject": "User",
                    "subject_type": "Person",
                    "predicate": "PERFORMED",
                    "object": action_description,
                    "object_type": "Action",
                    "confidence": 1.0,
                    "properties": {"outcome": outcome}
                }]
            }
        )
        response.raise_for_status()
        return {"success": True, "action_recorded": action_description}
    except Exception as e:
        return {"error": str(e), "success": False}


@tool
def get_smart_recommendation(user_id: str, category: str, query: str) -> dict:
    """
    Get a recommendation that respects both preferences AND constraints.
    
    This is the GraphRAG magic - it doesn't just find what the user likes,
    it finds what they like that also passes their current rules.
    
    Args:
        user_id: The user to recommend for
        category: Category of recommendation (Restaurant, Product, etc.)
        query: What they're looking for
    
    Returns:
        A recommendation with reasoning about why it was chosen
    """
    try:
        # First, load full context
        context_response = httpx.get(f"{API_BASE}/api/graph/context/{user_id}")
        context = context_response.json().get("context", {})
        
        # Check for conflicts
        conflict_response = httpx.post(
            f"{API_BASE}/api/graph/resolve-conflict",
            json={"user_id": user_id, "preference_type": category}
        )
        conflict_data = conflict_response.json().get("resolution", {})
        
        return {
            "context": context,
            "conflicts": conflict_data,
            "recommendation_ready": True
        }
    except Exception as e:
        return {"error": str(e)}

