"""
Phoenix Agent - Responder Node

Generates the final response after all steps are complete.
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agent.src.state import AgentState


RESPONDER_PROMPT = """You are the response component of the Phoenix Agent.
You've completed a task and need to summarize the results for the user.

Original Task: {task}

Steps Completed:
{steps_summary}

Conflicts Detected:
{conflicts}

Resolution Applied:
{resolution}

Provide a clear, friendly response to the user summarizing:
1. What was done
2. Any conflicts found between their preferences and constraints
3. How those conflicts were resolved
4. The final outcome

Be conversational and helpful."""


async def responder_node(state: AgentState) -> AgentState:
    """
    Generate the final response.
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.5)
    
    # Format steps summary
    steps = state.get("task_steps", [])
    steps_summary = "\n".join([
        f"  Step {s['step_number']}: {s['description']}\n    Result: {s.get('result', 'N/A')}"
        for s in steps
    ])
    
    # Format conflict info
    conflict = state.get("conflict_detected", {})
    conflict_str = str(conflict) if conflict else "None detected"
    
    resolution = state.get("resolution_applied", {})
    resolution_str = str(resolution) if resolution else "N/A"
    
    prompt = RESPONDER_PROMPT.format(
        task=state.get("current_task", "Unknown"),
        steps_summary=steps_summary,
        conflicts=conflict_str,
        resolution=resolution_str
    )
    
    response = await llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content="Generate the final response for the user.")
    ])
    
    return {
        **state,
        "final_response": response.content,
        "messages": state["messages"] + [response]
    }

