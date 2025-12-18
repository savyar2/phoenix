# 🧠 Phase 3: LangGraph Agent

**Estimated Time: 4-5 hours**

This phase builds the "Brain" - a stateful LangGraph agent that uses the Neo4j graph for context-aware reasoning.

---

## 3.1 Agent Architecture

The Phoenix Agent uses **LangGraph** for stateful, graph-based agent execution:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHOENIX AGENT (LangGraph)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    ┌──────────┐      ┌──────────┐      ┌──────────┐            │
│    │  START   │─────▶│  LOAD    │─────▶│  PLAN    │            │
│    │          │      │ CONTEXT  │      │          │            │
│    └──────────┘      └──────────┘      └────┬─────┘            │
│                                             │                    │
│                       ┌─────────────────────┼─────────────────┐ │
│                       │                     ▼                  │ │
│                       │              ┌──────────┐             │ │
│                       │              │ EXECUTE  │◀────────┐   │ │
│                       │              │   STEP   │         │   │ │
│                       │              └────┬─────┘         │   │ │
│                       │                   │               │   │ │
│    CHECKPOINT ────────┼───────────────────┤               │   │ │
│    (MemVerge)         │                   ▼               │   │ │
│                       │              ┌──────────┐         │   │ │
│                       │              │  VERIFY  │         │   │ │
│                       │              │  RESULT  │         │   │ │
│                       │              └────┬─────┘         │   │ │
│                       │                   │               │   │ │
│                       │         ┌─────────┴─────────┐     │   │ │
│                       │         ▼                   ▼     │   │ │
│                       │   [more steps?]        [done?]    │   │ │
│                       │         │                   │     │   │ │
│                       │         └───────────────────┘     │   │ │
│                       │                   │               │   │ │
│                       └───────────────────┼───────────────┘   │ │
│                                           ▼                    │ │
│                                    ┌──────────┐                │ │
│                                    │  RESPOND │                │ │
│                                    │          │                │ │
│                                    └──────────┘                │ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3.2 Agent State Definition

Create `agent/src/state.py`:

```python
"""
Phoenix Agent - State Definition

This defines the agent's working memory structure.
The state is what gets checkpointed by MemVerge.
"""
from typing import Annotated, Sequence, TypedDict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime
from pydantic import BaseModel, Field


class UserContext(TypedDict):
    """Context loaded from Neo4j graph."""
    user_id: str
    preferences: list[dict]
    constraints: list[dict]
    goals: list[dict]
    recent_actions: list[dict]
    conflicts: list[dict]


class TaskStep(TypedDict):
    """A single step in a multi-step task."""
    step_number: int
    description: str
    status: str  # pending, in_progress, completed, failed
    result: Any
    started_at: datetime | None
    completed_at: datetime | None


class AgentState(TypedDict):
    """
    The complete state of the Phoenix Agent.
    
    This entire structure is what gets frozen by MemVerge.
    On restore, the agent resumes exactly where it left off.
    """
    # Message history (LangGraph standard)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # User context from Neo4j
    user_context: UserContext | None
    
    # Current task information
    current_task: str | None
    task_steps: list[TaskStep]
    current_step_index: int
    total_steps: int
    
    # Execution tracking
    started_at: datetime | None
    last_checkpoint_at: datetime | None
    checkpoint_count: int
    
    # Decision state (for demos)
    pending_decision: dict | None
    conflict_detected: dict | None
    resolution_applied: dict | None
    
    # Final output
    final_response: str | None
    task_completed: bool


class CheckpointMetadata(BaseModel):
    """Metadata for a checkpoint (stored alongside MemVerge snapshot)."""
    checkpoint_id: str
    agent_state_hash: str
    step_number: int
    total_steps: int
    task_description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    memverge_snapshot_id: str | None = None
```

---

## 3.3 Agent Tools (Neo4j Integration)

Create `agent/src/tools/neo4j_tools.py`:

```python
"""
Phoenix Agent - Neo4j Tools

Tools for the agent to query and update the graph.
"""
from langchain_core.tools import tool
from typing import Any
import httpx

# Base URL for the Phoenix API
API_BASE = "http://api:8000"  # Docker service name


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
```

---

## 3.4 Agent Nodes

Create `agent/src/nodes/planner.py`:

```python
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
```

Create `agent/src/nodes/executor.py`:

```python
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
                if result.get("resolution") != "no_data":
                    state["conflict_detected"] = result
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
        "messages": state["messages"] + [response]
    }
```

Create `agent/src/nodes/verifier.py`:

```python
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


async def should_continue(state: AgentState) -> str:
    """
    Routing function: decide whether to continue executing or respond.
    """
    if state.get("task_completed", False):
        return "respond"
    
    current_idx = state.get("current_step_index", 0)
    total_steps = state.get("total_steps", 0)
    
    if current_idx >= total_steps:
        return "respond"
    
    return "execute"
```

Create `agent/src/nodes/responder.py`:

```python
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
```

---

## 3.5 LangGraph Definition

Create `agent/src/graph.py`:

```python
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


async def context_loader_node(state: AgentState) -> AgentState:
    """
    Load user context from Neo4j at the start of every task.
    """
    user_id = "demo_user"  # In production, extract from task
    context = load_user_context.invoke({"user_id": user_id})
    
    return {
        **state,
        "user_context": context,
        "started_at": datetime.utcnow(),
        "checkpoint_count": 0
    }


def create_phoenix_agent():
    """
    Create and compile the Phoenix Agent graph.
    
    Returns:
        Compiled LangGraph agent
    """
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("load_context", context_loader_node)
    workflow.add_node("plan", planner_node)
    workflow.add_node("execute", executor_node)
    workflow.add_node("verify", verifier_node)
    workflow.add_node("respond", responder_node)
    
    # Define edges
    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "verify")
    
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
```

---

## 3.6 Agent API Routes

Create `backend/app/api/routes/agent.py`:

```python
"""
Phoenix Protocol - Agent API Routes

Endpoints for controlling the LangGraph agent.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
from datetime import datetime
import uuid

router = APIRouter()

# Simple in-memory state tracking (replace with proper persistence)
agent_sessions = {}


class StartTaskRequest(BaseModel):
    """Request to start a new agent task."""
    task: str
    user_id: str = "demo_user"


class TaskStatusResponse(BaseModel):
    """Response with task status."""
    session_id: str
    status: str
    current_step: int
    total_steps: int
    steps_completed: list
    conflict_detected: dict | None
    final_response: str | None


async def run_agent_task(session_id: str, task: str, user_id: str):
    """Background task to run the agent."""
    from agent.src.graph import run_agent
    
    agent_sessions[session_id]["status"] = "running"
    
    try:
        final_state = await run_agent(task, user_id, session_id)
        
        agent_sessions[session_id].update({
            "status": "completed",
            "final_state": final_state,
            "current_step": final_state.get("current_step_index", 0),
            "total_steps": final_state.get("total_steps", 0),
            "final_response": final_state.get("final_response"),
            "conflict_detected": final_state.get("conflict_detected"),
            "completed_at": datetime.utcnow()
        })
    except Exception as e:
        agent_sessions[session_id]["status"] = "failed"
        agent_sessions[session_id]["error"] = str(e)


@router.post("/start")
async def start_task(request: StartTaskRequest, background_tasks: BackgroundTasks):
    """
    Start a new agent task.
    
    The agent runs in the background and can be monitored via /status.
    """
    session_id = str(uuid.uuid4())
    
    agent_sessions[session_id] = {
        "session_id": session_id,
        "task": request.task,
        "user_id": request.user_id,
        "status": "starting",
        "current_step": 0,
        "total_steps": 0,
        "steps_completed": [],
        "conflict_detected": None,
        "final_response": None,
        "started_at": datetime.utcnow(),
        "completed_at": None
    }
    
    background_tasks.add_task(run_agent_task, session_id, request.task, request.user_id)
    
    return {"session_id": session_id, "status": "started"}


@router.get("/status/{session_id}")
async def get_task_status(session_id: str):
    """
    Get the status of a running agent task.
    """
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = agent_sessions[session_id]
    
    return TaskStatusResponse(
        session_id=session_id,
        status=session["status"],
        current_step=session.get("current_step", 0),
        total_steps=session.get("total_steps", 0),
        steps_completed=session.get("steps_completed", []),
        conflict_detected=session.get("conflict_detected"),
        final_response=session.get("final_response")
    )


@router.get("/sessions")
async def list_sessions():
    """List all agent sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "task": s["task"],
                "status": s["status"],
                "started_at": s["started_at"]
            }
            for sid, s in agent_sessions.items()
        ]
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete an agent session."""
    if session_id in agent_sessions:
        del agent_sessions[session_id]
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Session not found")
```

---

## 3.7 Agent Container Setup

Create `agent/requirements.txt`:

```
langchain==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.1.0
langgraph==0.0.40
httpx==0.26.0
pydantic==2.5.3
structlog==24.1.0
```

Create `agent/Dockerfile.agent`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY src/ ./agent/src/

# Set Python path
ENV PYTHONPATH=/app

# Default command (overridden by orchestrator)
CMD ["python", "-c", "print('Agent container ready')"]
```

---

## 3.8 Demo Scenarios

Create `scripts/demo_scenario.py`:

```python
"""
Phoenix Protocol - Demo Scenario Runner

This script runs the key demo scenarios for the hackathon presentation.
"""
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000"


async def demo_conflict_resolution():
    """
    Demo 1: Show Neo4j conflict resolution
    
    Scenario: User asks for dinner reservation
    - User historically likes Steakhouse X
    - User recently started a "No Red Meat" diet
    - Graph should detect conflict and suggest alternative
    """
    print("\n" + "="*60)
    print("🥩 DEMO 1: Conflict Resolution (Neo4j Showcase)")
    print("="*60)
    
    # Start the task
    print("\n📝 Task: 'Book me a dinner reservation for tonight'")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/agent/start",
            json={
                "task": "Book me a dinner reservation for tonight",
                "user_id": "demo_user"
            }
        )
        session = response.json()
        session_id = session["session_id"]
        print(f"   Session started: {session_id}")
        
        # Poll for completion
        while True:
            await asyncio.sleep(2)
            status_response = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_response.json()
            
            print(f"   Status: {status['status']} - Step {status['current_step']}/{status['total_steps']}")
            
            if status["conflict_detected"]:
                print("\n🔴 CONFLICT DETECTED!")
                print(f"   {status['conflict_detected']}")
            
            if status["status"] in ["completed", "failed"]:
                break
        
        print("\n✅ Final Response:")
        print(f"   {status.get('final_response', 'No response')}")


async def demo_long_running_task():
    """
    Demo 2: Prepare for MemVerge crash/restore demo
    
    Scenario: Start a long-running task that will be "crashed"
    """
    print("\n" + "="*60)
    print("📊 DEMO 2: Long-Running Task (MemVerge Showcase Prep)")
    print("="*60)
    
    task = "Analyze my last 100 purchases and create a spending report with trends"
    
    print(f"\n📝 Task: '{task}'")
    print("   This task will take multiple steps...")
    print("   (We'll 'crash' the agent mid-way to demo MemVerge)")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/api/agent/start",
            json={
                "task": task,
                "user_id": "demo_user"
            }
        )
        session = response.json()
        session_id = session["session_id"]
        print(f"   Session started: {session_id}")
        
        # Show a few steps, then we'll "crash" it
        for i in range(5):
            await asyncio.sleep(3)
            status_response = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_response.json()
            
            print(f"   Step {status['current_step']}/{status['total_steps']}: {status['status']}")
            
            if i == 2:
                print("\n💥 SIMULATING CRASH... (Ctrl+C or kill the container)")
                print("   The agent is at step 3. MemVerge has checkpoints.")
                print("   Run the restore demo to bring it back!")
                break


if __name__ == "__main__":
    print("🔥 PHOENIX PROTOCOL - DEMO SCENARIOS")
    print("Choose a demo:")
    print("1. Conflict Resolution (Neo4j)")
    print("2. Long-Running Task (MemVerge prep)")
    
    choice = input("\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        asyncio.run(demo_conflict_resolution())
    elif choice == "2":
        asyncio.run(demo_long_running_task())
    else:
        print("Invalid choice")
```

---

## 3.9 Phase 3 Verification

### Test 1: Agent Graph Compiles
```bash
cd agent
python -c "
from src.graph import create_phoenix_agent
agent = create_phoenix_agent()
print('✅ Agent graph compiled successfully!')
print(f'   Nodes: {list(agent.nodes.keys())}')
"
```

### Test 2: Run Agent on Simple Task
```bash
curl -X POST http://localhost:8000/api/agent/start \
  -H "Content-Type: application/json" \
  -d '{"task": "What restaurants do I like?", "user_id": "demo_user"}'
```

### Test 3: Check Agent Status
```bash
curl http://localhost:8000/api/agent/status/{session_id}
```

---

## 3.10 Phase 3 Deliverables Checklist

- [ ] Agent state definition (what gets checkpointed)
- [ ] Neo4j tools for agent to query graph
- [ ] Planner node (breaks task into steps)
- [ ] Executor node (runs each step)
- [ ] Verifier node (checks progress)
- [ ] Responder node (generates final response)
- [ ] LangGraph definition with proper flow
- [ ] Agent API routes (start, status, list)
- [ ] Agent Docker container setup
- [ ] Demo scenario scripts

---

## Next: [Phase 4 - MemVerge Integration](./04-BUILD-PHASE-4-MEMVERGE.md)

