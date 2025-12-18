"""
Phoenix Agent - Planner Node

Analyzes the task and creates an execution plan.
"""
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from agent.src.state import AgentState, TaskStep
from datetime import datetime


PLANNER_PROMPT = """You are the planning component of the Phoenix Agent.
Your job is to break down a task into clear, executable steps.

User Context (from their memory graph):
{user_context}

Current Task: {task}

Create a numbered list of steps to complete this task.
Consider any conflicts between preferences and constraints.
Each step should be concrete and actionable.

Output format:
1. [Step description]
2. [Step description]
...

Keep it to 3-7 steps for most tasks."""


async def planner_node(state: AgentState) -> AgentState:
    """
    Plan the execution steps for the current task.
    """
    llm = ChatOpenAI(model="gpt-4", temperature=0.3)
    
    # Format user context for the prompt
    context_str = "No context loaded" if not state.get("user_context") else str(state["user_context"])
    
    prompt = PLANNER_PROMPT.format(
        user_context=context_str,
        task=state.get("current_task", "Unknown task")
    )
    
    response = await llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"Plan this task: {state.get('current_task')}")
    ])
    
    # Parse steps from response
    steps_text = response.content
    steps = []
    
    for i, line in enumerate(steps_text.strip().split('\n')):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-')):
            # Remove numbering/bullets
            step_desc = line.lstrip('0123456789.-) ').strip()
            if step_desc:
                steps.append(TaskStep(
                    step_number=i + 1,
                    description=step_desc,
                    status="pending",
                    result=None,
                    started_at=None,
                    completed_at=None
                ))
    
    return {
        **state,
        "task_steps": steps,
        "total_steps": len(steps),
        "current_step_index": 0,
        "messages": state["messages"] + [response]
    }

