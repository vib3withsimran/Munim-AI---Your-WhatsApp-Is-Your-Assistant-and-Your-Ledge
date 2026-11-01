from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MemoryEngine(ABC):
    """
    Abstract interface for Munim AI long-term memory engines (Meko, mock, in-memory).
    """

    @abstractmethod
    async def recall(
        self,
        datapack: str,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 5
    ) -> List[str]:
        """Recalls relevant memories or facts matching the query."""
        pass

    @abstractmethod
    async def write(
        self,
        datapack: str,
        text: str,
        agent_id: str = "CustomerAgent",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Stores a new fact or observation in long-term memory."""
        pass

    @abstractmethod
    async def promote(
        self,
        datapack: str,
        memory_id: str
    ) -> Dict[str, Any]:
        """Promotes an approved memory into durable business knowledge."""
        pass

