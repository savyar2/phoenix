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

