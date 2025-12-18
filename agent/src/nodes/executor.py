"""
Phoenix Agent - Executor Node

Executes individual steps of the plan.
"""
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agent.src.state import AgentState
from agent.src.tools.neo4j_tools import (
    load_user_context,
    check_for_conflicts,
    record_action,
    get_smart_recommendation
)
from datetime import datetime


EXECUTOR_PROMPT = """You are the execution component of the Phoenix Agent.
You are executing step {step_number} of {total_steps}: "{step_description}"

User Context:
{user_context}

Previous steps completed:
{previous_steps}

You have access to these tools:
- load_user_context: Get the user's preferences, constraints, and goals from their memory graph
- check_for_conflicts: Check if there are conflicts between what the user wants and their rules
- get_smart_recommendation: Get a recommendation that respects all user constraints
- record_action: Record what you did for future reference

Execute this step and provide the result. If you detect a conflict, explain it clearly."""


async def executor_node(state: AgentState) -> AgentState:
    """
    Execute the current step in the plan.
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.2)
    
    # Get current step
    current_idx = state.get("current_step_index", 0)
    steps = state.get("task_steps", [])
    
    if current_idx >= len(steps):
        return state
    
    current_step = steps[current_idx]
    
    # Mark step as in progress
    current_step["status"] = "in_progress"
    current_step["started_at"] = datetime.utcnow()
    
    # Format previous steps
    previous = "\n".join([
        f"  Step {s['step_number']}: {s['description']} -> {s.get('result', 'pending')}"
        for s in steps[:current_idx]
    ]) or "None"
    
    prompt = EXECUTOR_PROMPT.format(
        step_number=current_idx + 1,
        total_steps=len(steps),
        step_description=current_step["description"],
        user_context=str(state.get("user_context", {})),
        previous_steps=previous
    )
    
    # Execute with tool access
    tools = [load_user_context, check_for_conflicts, get_smart_recommendation, record_action]
    llm_with_tools = llm.bind_tools(tools)
    
    response = await llm_with_tools.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"Execute step: {current_step['description']}")
    ])
    
    # Handle tool calls if any
    conflict_detected = state.get("conflict_detected")
    if response.tool_calls:
        tool_results = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Execute the tool
            if tool_name == "load_user_context":
                result = load_user_context.invoke(tool_args)
            elif tool_name == "check_for_conflicts":
                result = check_for_conflicts.invoke(tool_args)
                # Store conflict for demo purposes
                if result.get("resolution") != "no_data" and result.get("resolution") != "unknown":
                    conflict_detected = result
            elif tool_name == "get_smart_recommendation":
                result = get_smart_recommendation.invoke(tool_args)
            elif tool_name == "record_action":
                result = record_action.invoke(tool_args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            tool_results.append({"tool": tool_name, "result": result})
        
        current_step["result"] = tool_results
    else:
        current_step["result"] = response.content
    
    # Mark step as completed
    current_step["status"] = "completed"
    current_step["completed_at"] = datetime.utcnow()
    
    # Update steps in state
    steps[current_idx] = current_step
    
    return {
        **state,
        "task_steps": steps,
        "current_step_index": current_idx + 1,
        "conflict_detected": conflict_detected,
        "messages": state["messages"] + [response]
    }

