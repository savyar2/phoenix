"""
Phoenix Protocol - MemMachine Integration Service

Handles persistent memory operations using MemMachine for AI agents.
MemMachine enables learning, storing, and recalling data from past sessions.
"""
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime

try:
    # Try different import paths for MemMachine client
    try:
        from memmachine.rest_client import MemMachineClient
    except ImportError:
        try:
            from memmachine import MemMachineClient
        except ImportError:
            MemMachineClient = None
except Exception:
    # If package is installed but broken, set to None
    MemMachineClient = None

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class MemMachineService:
    """
    Service for MemMachine memory operations.
    
    Provides persistent memory layer for AI agents across sessions.
    """
    
    _client: Optional[Any] = None
    _initialized: bool = False
    
    @classmethod
    def get_client(cls) -> Optional[Any]:
        """Get or create MemMachine client instance."""
        if not settings.memmachine_enabled:
            logger.warning("MemMachine is disabled in configuration")
            return None
            
        if MemMachineClient is None:
            logger.error("memmachine-client package not installed. Run: pip install memmachine-client")
            return None
        
        if cls._client is None:
            try:
                cls._client = MemMachineClient(
                    api_key=settings.memmachine_api_key,
                    base_url=settings.memmachine_base_url
                )
                cls._initialized = True
                logger.info(
                    "MemMachine client initialized",
                    base_url=settings.memmachine_base_url
                )
            except Exception as e:
                logger.error(f"Failed to initialize MemMachine client: {e}")
                return None
        
        return cls._client
    
    @classmethod
    async def store_memory(
        cls,
        user_id: str,
        memory_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store a memory in MemMachine.
        
        Args:
            user_id: Unique identifier for the user
            memory_type: Type of memory (episodic, profile, etc.)
            content: The memory content to store
            metadata: Optional metadata dictionary
        
        Returns:
            Memory ID if successful, None otherwise
        """
        client = cls.get_client()
        if client is None:
            return None
        
        try:
            # MemMachine API structure may vary - adjust based on actual API
            memory_data = {
                "user_id": user_id,
                "type": memory_type,
                "content": content,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store memory using MemMachine client
            # Note: Adjust method names based on actual MemMachine API
            result = client.store_memory(**memory_data)
            
            logger.info(
                "Memory stored in MemMachine",
                user_id=user_id,
                memory_type=memory_type
            )
            
            return result.get("memory_id") if isinstance(result, dict) else str(result)
            
        except Exception as e:
            logger.error(f"Failed to store memory in MemMachine: {e}")
            return None
    
    @classmethod
    async def recall_memories(
        cls,
        user_id: str,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recall relevant memories from MemMachine.
        
        Args:
            user_id: Unique identifier for the user
            query: Query to search for relevant memories
            memory_type: Optional filter by memory type
            limit: Maximum number of memories to return
        
        Returns:
            List of relevant memories
        """
        client = cls.get_client()
        if client is None:
            return []
        
        try:
            # Query memories using MemMachine client
            # Note: Adjust method names based on actual MemMachine API
            result = client.recall_memories(
                user_id=user_id,
                query=query,
                memory_type=memory_type,
                limit=limit
            )
            
            memories = result if isinstance(result, list) else result.get("memories", [])
            
            logger.info(
                "Memories recalled from MemMachine",
                user_id=user_id,
                count=len(memories)
            )
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to recall memories from MemMachine: {e}")
            return []
    
    @classmethod
    async def update_user_profile(
        cls,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> bool:
        """
        Update user profile in MemMachine.
        
        Args:
            user_id: Unique identifier for the user
            profile_data: Profile data to update
        
        Returns:
            True if successful, False otherwise
        """
        client = cls.get_client()
        if client is None:
            return False
        
        try:
            # Update profile using MemMachine client
            # Note: Adjust method names based on actual MemMachine API
            client.update_profile(user_id=user_id, **profile_data)
            
            logger.info("User profile updated in MemMachine", user_id=user_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile in MemMachine: {e}")
            return False
    
    @classmethod
    async def get_user_profile(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from MemMachine.
        
        Args:
            user_id: Unique identifier for the user
        
        Returns:
            User profile dictionary or None
        """
        client = cls.get_client()
        if client is None:
            return None
        
        try:
            # Get profile using MemMachine client
            # Note: Adjust method names based on actual MemMachine API
            profile = client.get_profile(user_id=user_id)
            
            return profile if isinstance(profile, dict) else None
            
        except Exception as e:
            logger.error(f"Failed to get user profile from MemMachine: {e}")
            return None
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """
        Check MemMachine service health.
        
        Returns:
            Health status dictionary
        """
        if not settings.memmachine_enabled:
            return {
                "status": "disabled",
                "enabled": False
            }
        
        client = cls.get_client()
        if client is None:
            return {
                "status": "unavailable",
                "enabled": True,
                "error": "Client not initialized"
            }
        
        try:
            # Check health using MemMachine client
            # Note: Adjust method names based on actual MemMachine API
            health = client.health_check() if hasattr(client, "health_check") else None
            
            return {
                "status": "healthy" if health else "unknown",
                "enabled": True,
                "base_url": settings.memmachine_base_url,
                "initialized": cls._initialized
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "enabled": True,
                "error": str(e)
            }

