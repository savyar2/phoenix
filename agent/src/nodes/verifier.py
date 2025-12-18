"""
Phoenix Agent - Verifier Node

Verifies step results and decides whether to continue or respond.
"""
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from agent.src.state import AgentState


async def verifier_node(state: AgentState) -> AgentState:
    """
    Verify the result of the last step and update state.
    """
    current_idx = state.get("current_step_index", 0)
    total_steps = state.get("total_steps", 0)
    
    # Check if we're done
    if current_idx >= total_steps:
        state["task_completed"] = True
    
    return state


def should_continue(state: AgentState) -> str:
    """
    Routing function: decide whether to continue executing or respond.
    
    This is a synchronous function used by LangGraph's conditional edges.
    """
    if state.get("task_completed", False):
        return "respond"
    
    current_idx = state.get("current_step_index", 0)
    total_steps = state.get("total_steps", 0)
    
    if current_idx >= total_steps:
        return "respond"
    
    return "execute"

