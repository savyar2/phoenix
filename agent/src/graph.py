"""
Phoenix Agent - LangGraph Definition

This defines the agent's execution graph.
"""
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from agent.src.state import AgentState
from agent.src.nodes.planner import planner_node
from agent.src.nodes.executor import executor_node
from agent.src.nodes.verifier import verifier_node, should_continue
from agent.src.nodes.responder import responder_node
from agent.src.tools.neo4j_tools import load_user_context
from datetime import datetime
import httpx

API_BASE = "http://api:8000"  # Docker service name, or use environment variable
CHECKPOINT_INTERVAL = 30  # seconds


async def context_loader_node(state: AgentState) -> AgentState:
    """
    Load user context from Neo4j at the start of every task.
    """
    user_id = state.get("user_id", "demo_user")
    context = load_user_context.invoke({"user_id": user_id})
    
    return {
        **state,
        "user_context": context,
        "started_at": datetime.utcnow(),
        "checkpoint_count": 0
    }


async def checkpoint_node(state: AgentState) -> AgentState:
    """
    Checkpoint node - creates a MemVerge snapshot of current state.
    
    This is called between execution steps to ensure recoverability.
    """
    # Check if enough time has passed since last checkpoint
    last_checkpoint = state.get("last_checkpoint_at")
    now = datetime.utcnow()
    
    if last_checkpoint:
        elapsed = (now - last_checkpoint).total_seconds()
        if elapsed < CHECKPOINT_INTERVAL:
            return state  # Skip, not enough time
    
    # Create checkpoint
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE}/api/memverge/checkpoint",
                json={
                    "container_id": "phoenix-agent",
                    "step_number": state.get("current_step_index", 0),
                    "total_steps": state.get("total_steps", 0),
                    "task_description": state.get("current_task", "Unknown")
                },
                timeout=10.0
            )
            response.raise_for_status()
            
            return {
                **state,
                "last_checkpoint_at": now,
                "checkpoint_count": state.get("checkpoint_count", 0) + 1
            }
    except Exception as e:
        # Log but don't fail the agent on checkpoint errors
        print(f"Checkpoint failed: {e}")
        return state


def create_phoenix_agent():
    """
    Create and compile the Phoenix Agent graph with checkpointing.
    
    Returns:
        Compiled LangGraph agent
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes including checkpoint
    workflow.add_node("load_context", context_loader_node)
    workflow.add_node("plan", planner_node)
    workflow.add_node("execute", executor_node)
    workflow.add_node("checkpoint", checkpoint_node)  # NEW
    workflow.add_node("verify", verifier_node)
    workflow.add_node("respond", responder_node)
    
    # Define edges with checkpoint after execute
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "checkpoint")  # Checkpoint after each step
    workflow.add_edge("checkpoint", "verify")
    
    # Conditional edge: continue executing or respond
    workflow.add_conditional_edges(
        "verify",
        should_continue,
        {
            "execute": "execute",
            "respond": "respond"
        }
    )
    
    workflow.add_edge("respond", END)
    
    # Create checkpointer for state persistence
    # In production, this would be backed by MemVerge
    checkpointer = MemorySaver()
    
    # Compile the graph
    agent = workflow.compile(checkpointer=checkpointer)
    
    return agent


# Create the global agent instance
phoenix_agent = create_phoenix_agent()


async def run_agent(task: str, user_id: str = "demo_user", thread_id: str = "default"):
    """
    Run the Phoenix Agent on a task.
    
    Args:
        task: The task to perform
        user_id: The user ID for context loading
        thread_id: Thread ID for checkpointing
    
    Returns:
        Final agent state
    """
    initial_state = AgentState(
        messages=[],
        user_id=user_id,
        user_context=None,
        current_task=task,
        task_steps=[],
        current_step_index=0,
        total_steps=0,
        started_at=None,
        last_checkpoint_at=None,
        checkpoint_count=0,
        pending_decision=None,
        conflict_detected=None,
        resolution_applied=None,
        final_response=None,
        task_completed=False
    )
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run the agent
    final_state = await phoenix_agent.ainvoke(initial_state, config)
    
    return final_state


async def get_agent_state(thread_id: str = "default"):
    """
    Get the current state of an agent thread.
    
    This is used for the dashboard to show agent progress.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state = await phoenix_agent.aget_state(config)
    return state

