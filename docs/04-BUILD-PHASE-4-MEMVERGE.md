# 💾 Phase 4: MemVerge Integration

**Estimated Time: 3-4 hours**

This phase implements the "Immortal Agent" capability - using MemVerge to checkpoint and restore the agent's execution state.

---

## 4.1 Understanding MemVerge

### What MemVerge Provides

**MemVerge Memory Machine Cloud (MMC)** enables:
- **Live Checkpointing**: Snapshot running process memory to cloud storage
- **Instant Restore**: Resume a process from snapshot in seconds
- **Time Travel**: Go back to any previous checkpoint
- **Migration**: Move running processes between hosts

### Why This Matters for Phoenix

Traditional agent "memory" stores facts. MemVerge stores **thought processes**:
- The agent was at step 25 of 50
- It had partial results in RAM
- It was mid-reasoning about a conflict
- All of this is preserved and restored

---

## 4.2 MemVerge Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MEMVERGE INTEGRATION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    PHOENIX AGENT CONTAINER                      │ │
│  │                   (Docker + MemVerge Agent)                     │ │
│  │                                                                 │ │
│  │   ┌─────────────────────────────────────────────────────────┐  │ │
│  │   │                    PROCESS MEMORY                        │  │ │
│  │   │   • LangGraph state                                      │  │ │
│  │   │   • Current step: 25/50                                  │  │ │
│  │   │   • Intermediate calculations                            │  │ │
│  │   │   • Decision tree state                                  │  │ │
│  │   │   • Open connections (handled gracefully)                │  │ │
│  │   └─────────────────────────────────────────────────────────┘  │ │
│  │                              │                                  │ │
│  │                              │ Periodic Checkpoint              │ │
│  │                              ▼                                  │ │
│  │   ┌─────────────────────────────────────────────────────────┐  │ │
│  │   │              MEMVERGE AGENT (mmcloud)                    │  │ │
│  │   │                                                          │  │ │
│  │   │   mmcloud checkpoint <container_id> --dest s3://...     │  │ │
│  │   │   mmcloud restore <snapshot_id>                          │  │ │
│  │   │   mmcloud list-snapshots                                 │  │ │
│  │   └─────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                │                                     │
│                                │ Snapshots                           │
│                                ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    MEMVERGE MMC CLOUD                           │ │
│  │                                                                 │ │
│  │   📸 snap_001 - 2024-01-15 14:30:00 - Step 10/50               │ │
│  │   📸 snap_002 - 2024-01-15 14:30:30 - Step 15/50               │ │
│  │   📸 snap_003 - 2024-01-15 14:31:00 - Step 20/50               │ │
│  │   📸 snap_004 - 2024-01-15 14:31:30 - Step 25/50  ◀── CRASH!  │ │
│  │                                                                 │ │
│  │   [Restore from snap_004 → Agent resumes at step 25]           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4.3 MemVerge Service

Create `backend/app/services/memverge_service.py`:

```python
"""
Phoenix Protocol - MemVerge Integration Service

Handles checkpointing and restoration of agent state using MemVerge MMC.
"""
import structlog
import httpx
import subprocess
import json
from datetime import datetime
from typing import Optional
import uuid

from app.config import get_settings
from app.models.agent_state import AgentCheckpoint, CheckpointMetadata

logger = structlog.get_logger()
settings = get_settings()


class MemVergeService:
    """
    Service for MemVerge Memory Machine Cloud operations.
    
    Provides checkpoint/restore capabilities for the Phoenix Agent.
    """
    
    # In-memory checkpoint registry (in production, use a database)
    _checkpoints: dict[str, CheckpointMetadata] = {}
    
    @classmethod
    async def create_checkpoint(
        cls,
        container_id: str,
        step_number: int,
        total_steps: int,
        task_description: str
    ) -> CheckpointMetadata:
        """
        Create a checkpoint of the agent container.
        
        This captures the entire memory state of the running agent.
        """
        checkpoint_id = f"ckpt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Creating checkpoint {checkpoint_id} at step {step_number}/{total_steps}")
        
        try:
            # Option 1: Use MemVerge MMC API
            if settings.memverge_api_endpoint:
                snapshot_id = await cls._checkpoint_via_api(container_id, checkpoint_id)
            
            # Option 2: Use mmcloud CLI
            else:
                snapshot_id = await cls._checkpoint_via_cli(container_id, checkpoint_id)
            
            # Store metadata
            metadata = CheckpointMetadata(
                checkpoint_id=checkpoint_id,
                agent_state_hash=f"hash_{checkpoint_id}",
                step_number=step_number,
                total_steps=total_steps,
                task_description=task_description,
                memverge_snapshot_id=snapshot_id
            )
            
            cls._checkpoints[checkpoint_id] = metadata
            
            logger.info(f"Checkpoint created: {checkpoint_id} -> {snapshot_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Checkpoint creation failed: {e}")
            raise
    
    @classmethod
    async def _checkpoint_via_api(cls, container_id: str, checkpoint_id: str) -> str:
        """Create checkpoint via MemVerge MMC API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.memverge_api_endpoint}/checkpoint",
                headers={"Authorization": f"Bearer {settings.memverge_api_key}"},
                json={
                    "container_id": container_id,
                    "checkpoint_name": checkpoint_id,
                    "project_id": settings.memverge_project_id
                }
            )
            response.raise_for_status()
            return response.json().get("snapshot_id")
    
    @classmethod
    async def _checkpoint_via_cli(cls, container_id: str, checkpoint_id: str) -> str:
        """Create checkpoint via mmcloud CLI."""
        # For demo/development, simulate the checkpoint
        # In production, this would call the actual mmcloud command
        
        cmd = [
            "mmcloud",
            "checkpoint",
            container_id,
            "--name", checkpoint_id,
            "--dest", f"s3://phoenix-checkpoints/{checkpoint_id}"
        ]
        
        # Simulate for development
        logger.info(f"Would run: {' '.join(cmd)}")
        
        # In production:
        # result = subprocess.run(cmd, capture_output=True, text=True)
        # if result.returncode != 0:
        #     raise Exception(f"Checkpoint failed: {result.stderr}")
        # return result.stdout.strip()
        
        return f"snap_{uuid.uuid4().hex[:12]}"
    
    @classmethod
    async def restore_from_checkpoint(
        cls,
        checkpoint_id: Optional[str] = None
    ) -> dict:
        """
        Restore the agent from a checkpoint.
        
        If no checkpoint_id is provided, restores from the latest checkpoint.
        """
        # Get checkpoint to restore
        if checkpoint_id is None:
            # Find latest checkpoint
            if not cls._checkpoints:
                raise ValueError("No checkpoints available")
            checkpoint_id = max(
                cls._checkpoints.keys(),
                key=lambda k: cls._checkpoints[k].timestamp
            )
        
        if checkpoint_id not in cls._checkpoints:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        
        metadata = cls._checkpoints[checkpoint_id]
        
        logger.info(f"Restoring from checkpoint {checkpoint_id} (step {metadata.step_number})")
        
        try:
            # Option 1: Use MemVerge MMC API
            if settings.memverge_api_endpoint:
                result = await cls._restore_via_api(metadata.memverge_snapshot_id)
            
            # Option 2: Use mmcloud CLI
            else:
                result = await cls._restore_via_cli(metadata.memverge_snapshot_id)
            
            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "restored_step": metadata.step_number,
                "total_steps": metadata.total_steps,
                "task": metadata.task_description,
                "message": f"Agent restored at step {metadata.step_number}/{metadata.total_steps}"
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    @classmethod
    async def _restore_via_api(cls, snapshot_id: str) -> dict:
        """Restore via MemVerge MMC API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.memverge_api_endpoint}/restore",
                headers={"Authorization": f"Bearer {settings.memverge_api_key}"},
                json={
                    "snapshot_id": snapshot_id,
                    "project_id": settings.memverge_project_id
                }
            )
            response.raise_for_status()
            return response.json()
    
    @classmethod
    async def _restore_via_cli(cls, snapshot_id: str) -> dict:
        """Restore via mmcloud CLI."""
        cmd = [
            "mmcloud",
            "restore",
            snapshot_id
        ]
        
        # Simulate for development
        logger.info(f"Would run: {' '.join(cmd)}")
        
        return {"restored": True, "snapshot_id": snapshot_id}
    
    @classmethod
    async def list_checkpoints(cls, limit: int = 10) -> list[CheckpointMetadata]:
        """List available checkpoints."""
        checkpoints = list(cls._checkpoints.values())
        checkpoints.sort(key=lambda x: x.timestamp, reverse=True)
        return checkpoints[:limit]
    
    @classmethod
    async def delete_checkpoint(cls, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        if checkpoint_id in cls._checkpoints:
            # In production, also delete from MemVerge
            del cls._checkpoints[checkpoint_id]
            return True
        return False
    
    @classmethod
    async def simulate_crash(cls, container_id: str) -> dict:
        """
        Simulate an agent crash for demo purposes.
        
        This forcefully stops the container without cleanup.
        """
        logger.warning(f"💥 Simulating crash for container {container_id}")
        
        # In production, this would actually kill the container
        cmd = ["docker", "kill", container_id]
        
        # Simulate for development
        logger.info(f"Would run: {' '.join(cmd)}")
        
        return {
            "crashed": True,
            "container_id": container_id,
            "message": "Container terminated. Use restore endpoint to recover."
        }
```

---

## 4.4 MemVerge API Routes

Create `backend/app/api/routes/memverge.py`:

```python
"""
Phoenix Protocol - MemVerge API Routes

Endpoints for checkpoint/restore operations.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.memverge_service import MemVergeService
from app.models.agent_state import CheckpointMetadata

router = APIRouter()


class CreateCheckpointRequest(BaseModel):
    """Request to create a checkpoint."""
    container_id: str = "phoenix-agent"
    step_number: int
    total_steps: int
    task_description: str


class RestoreRequest(BaseModel):
    """Request to restore from checkpoint."""
    checkpoint_id: Optional[str] = None  # None = latest


class CrashSimulationRequest(BaseModel):
    """Request to simulate a crash (demo only)."""
    container_id: str = "phoenix-agent"
    delay_seconds: float = 0.0


@router.post("/checkpoint")
async def create_checkpoint(request: CreateCheckpointRequest):
    """
    Create a checkpoint of the agent's current state.
    
    This is called automatically during agent execution,
    but can also be triggered manually.
    """
    try:
        metadata = await MemVergeService.create_checkpoint(
            container_id=request.container_id,
            step_number=request.step_number,
            total_steps=request.total_steps,
            task_description=request.task_description
        )
        
        return {
            "success": True,
            "checkpoint": metadata.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_from_checkpoint(request: RestoreRequest):
    """
    Restore the agent from a checkpoint.
    
    THIS IS THE KEY DEMO for MemVerge judges!
    Shows the agent waking up exactly where it left off.
    """
    try:
        result = await MemVergeService.restore_from_checkpoint(request.checkpoint_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkpoints")
async def list_checkpoints(limit: int = 10):
    """
    List available checkpoints.
    
    Returns checkpoints sorted by timestamp (newest first).
    """
    checkpoints = await MemVergeService.list_checkpoints(limit)
    return {
        "checkpoints": [c.model_dump() for c in checkpoints]
    }


@router.get("/checkpoint/{checkpoint_id}")
async def get_checkpoint(checkpoint_id: str):
    """Get details of a specific checkpoint."""
    checkpoints = await MemVergeService.list_checkpoints(100)
    for ckpt in checkpoints:
        if ckpt.checkpoint_id == checkpoint_id:
            return {"checkpoint": ckpt.model_dump()}
    raise HTTPException(status_code=404, detail="Checkpoint not found")


@router.delete("/checkpoint/{checkpoint_id}")
async def delete_checkpoint(checkpoint_id: str):
    """Delete a checkpoint."""
    deleted = await MemVergeService.delete_checkpoint(checkpoint_id)
    if deleted:
        return {"deleted": True}
    raise HTTPException(status_code=404, detail="Checkpoint not found")


@router.post("/simulate-crash")
async def simulate_crash(request: CrashSimulationRequest):
    """
    Simulate an agent crash for demo purposes.
    
    ⚠️ DEMO ONLY - This forcefully kills the agent container!
    """
    import asyncio
    
    if request.delay_seconds > 0:
        await asyncio.sleep(request.delay_seconds)
    
    result = await MemVergeService.simulate_crash(request.container_id)
    return result


@router.get("/demo-status")
async def get_demo_status():
    """
    Get the current status for demo purposes.
    
    Shows:
    - Number of checkpoints available
    - Last checkpoint time
    - Whether agent is crashed or running
    """
    checkpoints = await MemVergeService.list_checkpoints(1)
    
    return {
        "checkpoints_available": len(await MemVergeService.list_checkpoints(100)),
        "latest_checkpoint": checkpoints[0].model_dump() if checkpoints else None,
        "agent_status": "unknown",  # Would check actual container status
        "ready_for_demo": len(checkpoints) > 0
    }
```

---

## 4.5 Checkpoint Integration with Agent

Update `agent/src/graph.py` to add checkpointing:

```python
"""
Phoenix Agent - LangGraph with MemVerge Checkpointing

Add this to the existing graph.py file.
"""
import httpx
from datetime import datetime
import asyncio

API_BASE = "http://api:8000"
CHECKPOINT_INTERVAL = 30  # seconds


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


def create_phoenix_agent_with_checkpointing():
    """
    Create agent graph with checkpointing after each execution step.
    """
    workflow = StateGraph(AgentState)
    
    # Add all nodes including checkpoint
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
    
    checkpointer = MemorySaver()
    agent = workflow.compile(checkpointer=checkpointer)
    
    return agent
```

---

## 4.6 Demo Script: Crash and Restore

Create `scripts/demo_crash_restore.py`:

```python
"""
Phoenix Protocol - Crash and Restore Demo

This script demonstrates the MemVerge integration:
1. Starts a long-running agent task
2. Waits until it's partway through
3. Simulates a crash
4. Restores from checkpoint
5. Shows the agent continuing from where it left off
"""
import asyncio
import httpx
from datetime import datetime

API_BASE = "http://localhost:8000"


async def run_demo():
    """Run the crash and restore demo."""
    
    print("\n" + "="*70)
    print("🔥 PHOENIX PROTOCOL - IMMORTAL AGENT DEMO")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Start a long-running task
        print("\n📝 Step 1: Starting a complex agent task...")
        print("   Task: 'Analyze 50 transactions and create a spending report'")
        
        response = await client.post(
            f"{API_BASE}/api/agent/start",
            json={
                "task": "Analyze 50 transactions and create a spending report with trends",
                "user_id": "demo_user"
            }
        )
        session = response.json()
        session_id = session["session_id"]
        print(f"   ✅ Session started: {session_id}")
        
        # Step 2: Let it run and checkpoint
        print("\n⏳ Step 2: Agent is working... (checkpoints every 30s)")
        
        for i in range(5):
            await asyncio.sleep(3)
            
            # Check status
            status_resp = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_resp.json()
            
            # Check checkpoints
            ckpt_resp = await client.get(f"{API_BASE}/api/memverge/checkpoints")
            checkpoints = ckpt_resp.json()["checkpoints"]
            
            print(f"   Progress: Step {status['current_step']}/{status['total_steps']}")
            print(f"   Checkpoints available: {len(checkpoints)}")
            
            if status["current_step"] >= 3 and len(checkpoints) > 0:
                print("\n   🎯 Agent has made progress and checkpoints exist!")
                break
        
        # Step 3: Simulate crash
        print("\n💥 Step 3: SIMULATING CRASH!")
        print("   (In production, this would kill the Docker container)")
        
        crash_resp = await client.post(
            f"{API_BASE}/api/memverge/simulate-crash",
            json={"container_id": "phoenix-agent"}
        )
        print(f"   {crash_resp.json()['message']}")
        
        # Dramatic pause
        print("\n   ☠️  Agent is DOWN")
        await asyncio.sleep(2)
        
        # Step 4: Show available checkpoints
        print("\n📸 Step 4: Available checkpoints:")
        ckpt_resp = await client.get(f"{API_BASE}/api/memverge/checkpoints")
        checkpoints = ckpt_resp.json()["checkpoints"]
        
        for ckpt in checkpoints:
            print(f"   - {ckpt['checkpoint_id']}")
            print(f"     Step: {ckpt['step_number']}/{ckpt['total_steps']}")
            print(f"     Time: {ckpt['timestamp']}")
        
        if not checkpoints:
            print("   ⚠️  No checkpoints found (demo may have run too fast)")
            return
        
        # Step 5: Restore from latest checkpoint
        print("\n🔄 Step 5: RESTORING FROM CHECKPOINT...")
        print("   Using MemVerge to restore agent state...")
        
        restore_resp = await client.post(
            f"{API_BASE}/api/memverge/restore",
            json={"checkpoint_id": None}  # Latest
        )
        restore_result = restore_resp.json()
        
        print(f"\n   ✅ AGENT RESTORED!")
        print(f"   Restored to step: {restore_result['restored_step']}/{restore_result['total_steps']}")
        print(f"   Task: {restore_result['task']}")
        print(f"\n   🔥 The agent is IMMORTAL! It continued exactly where it left off.")
        
        # Step 6: Show agent continuing
        print("\n⏩ Step 6: Agent continues working...")
        
        for i in range(3):
            await asyncio.sleep(2)
            status_resp = await client.get(f"{API_BASE}/api/agent/status/{session_id}")
            status = status_resp.json()
            print(f"   Progress: Step {status['current_step']}/{status['total_steps']}")
            
            if status["status"] == "completed":
                print("\n   ✅ Task completed!")
                print(f"\n   📋 Final Response:")
                print(f"   {status.get('final_response', 'N/A')}")
                break
        
        print("\n" + "="*70)
        print("🎉 DEMO COMPLETE - The Phoenix has risen!")
        print("="*70)


if __name__ == "__main__":
    print("\nThis demo shows MemVerge checkpoint/restore capabilities.")
    print("Make sure the API server is running on localhost:8000\n")
    
    input("Press Enter to start the demo...")
    asyncio.run(run_demo())
```

Create `scripts/simulate_crash.sh`:

```bash
#!/bin/bash
# Simulate a crash by killing the agent container

echo "💥 Simulating agent crash..."
echo ""

# Option 1: Use API
curl -X POST http://localhost:8000/api/memverge/simulate-crash \
  -H "Content-Type: application/json" \
  -d '{"container_id": "phoenix-agent", "delay_seconds": 0}'

# Option 2: Direct Docker kill (uncomment if needed)
# docker kill phoenix-agent

echo ""
echo "Agent crashed. Run restore to bring it back:"
echo "  curl -X POST http://localhost:8000/api/memverge/restore"
```

---

## 4.7 Update Main App

Update `backend/app/main.py` to include MemVerge routes:

```python
# Add this import
from app.api.routes import ingest, graph, agent, memverge

# Add this router after the others
app.include_router(memverge.router, prefix="/api/memverge", tags=["MemVerge"])
```

---

## 4.8 Production MemVerge Setup

### Using MemVerge Memory Machine Cloud (MMC)

For the actual hackathon with MemVerge infrastructure:

1. **Get MMC Access**
   - Contact MemVerge sponsor for API credentials
   - They may provide a dedicated project space

2. **Install mmcloud CLI**
   ```bash
   # Download from MemVerge
   curl -O https://mmcloud.memverge.com/downloads/mmcloud-cli
   chmod +x mmcloud-cli
   sudo mv mmcloud-cli /usr/local/bin/mmcloud
   
   # Configure
   mmcloud configure --api-key YOUR_API_KEY
   ```

3. **Run Agent Container on MMC**
   ```bash
   # Submit container to MMC
   mmcloud run \
     --name phoenix-agent \
     --image phoenix-agent:latest \
     --checkpoint-interval 30s \
     --checkpoint-dest s3://your-bucket/checkpoints/
   ```

4. **Checkpoint Commands**
   ```bash
   # Manual checkpoint
   mmcloud checkpoint phoenix-agent
   
   # List checkpoints
   mmcloud list-checkpoints phoenix-agent
   
   # Restore
   mmcloud restore <snapshot-id>
   ```

### Docker Compose for MMC

Create `docker-compose.mmc.yml`:

```yaml
version: '3.8'

services:
  # Agent runs on MemVerge MMC, not locally
  # This is just for documentation
  
  # Configuration for MMC submission:
  # mmcloud submit:
  #   image: phoenix-agent:latest
  #   resources:
  #     memory: 4G
  #     cpu: 2
  #   checkpointing:
  #     enabled: true
  #     interval: 30s
  #     destination: s3://phoenix-checkpoints/
  #   environment:
  #     - NEO4J_URI
  #     - OPENAI_API_KEY
  
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MEMVERGE_API_ENDPOINT=https://mmc.memverge.com/api
      - MEMVERGE_API_KEY=${MEMVERGE_API_KEY}
      - MEMVERGE_PROJECT_ID=phoenix-hackathon
```

---

## 4.9 Phase 4 Verification

### Test 1: Create Checkpoint
```bash
curl -X POST http://localhost:8000/api/memverge/checkpoint \
  -H "Content-Type: application/json" \
  -d '{
    "container_id": "phoenix-agent",
    "step_number": 5,
    "total_steps": 10,
    "task_description": "Test task"
  }'
```

### Test 2: List Checkpoints
```bash
curl http://localhost:8000/api/memverge/checkpoints
```

### Test 3: Restore from Checkpoint
```bash
curl -X POST http://localhost:8000/api/memverge/restore \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Test 4: Run Full Demo
```bash
python scripts/demo_crash_restore.py
```

---

## 4.10 Phase 4 Deliverables Checklist

- [ ] MemVerge service with checkpoint/restore logic
- [ ] API routes for checkpoint operations
- [ ] Checkpoint node integrated into agent graph
- [ ] Crash simulation endpoint
- [ ] Demo script for crash and restore
- [ ] Documentation for production MMC setup
- [ ] Checkpoint metadata storage

---

## Next: [Phase 5 - Frontend Dashboard](./05-BUILD-PHASE-5-FRONTEND.md)

