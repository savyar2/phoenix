"""
Phoenix Protocol - Agent API Routes

Endpoints for controlling the LangGraph agent.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
from datetime import datetime
import uuid
import sys
import os
from pathlib import Path

# Add agent directory to path for imports
# Get the project root (4 levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent.parent
agent_path = project_root / "agent"
sys.path.insert(0, str(agent_path))

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
    try:
        from agent.src.graph import run_agent
        
        agent_sessions[session_id]["status"] = "running"
        
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

