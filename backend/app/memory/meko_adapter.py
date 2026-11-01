import json
import uuid
import logging
import httpx
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings
from backend.app.memory.interface import MemoryEngine

logger = logging.getLogger(__name__)

MEKO_MCP_URL = "https://mcp.mekodata.ai/mcp"

# Datapack UUID mapping
DATAPACK_MAP = {
    "build": settings.MEKO_DATAPACK_BUILD or "0491c3bb-05a2-4e7c-9f02-741b327cd80a",
    "customer": settings.MEKO_DATAPACK_CUSTOMER or "176d3ad2-4495-406b-ad41-715488de7713",
    "orders": settings.MEKO_DATAPACK_ORDERS or "2bf91f49-255b-45fc-acd7-a22272bfa3f7",
    "finance": settings.MEKO_DATAPACK_FINANCE or "f6862f0f-8e0d-43b4-b78d-5eb250edb8a2"
}

class MekoAdapter(MemoryEngine):
    """
    Production Meko Long-Term Memory Adapter for Munim AI.
    Integrates directly with Meko MCP over streamable HTTP.
    """

    def __init__(self, api_key: Optional[str] = None, enabled: bool = True):
        self.api_key = api_key or settings.MEKO_API_KEY
        self.enabled = enabled
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }

    def _resolve_datapack_id(self, datapack_name_or_id: str) -> str:
        key = datapack_name_or_id.lower().replace("munim-", "").strip()
        return DATAPACK_MAP.get(key, datapack_name_or_id)

    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any], timeout: float = 12.0) -> Dict[str, Any]:
        """Calls a tool on Meko MCP via JSON-RPC."""
        if not self.enabled or not self.api_key:
            return {}

        payload = {
            "jsonrpc": "2.0",
            "id": int(uuid.uuid4().int % 100000),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(MEKO_MCP_URL, headers=self._headers, json=payload)
                if res.status_code == 200:
                    for line in res.text.splitlines():
                        if line.startswith("data:"):
                            raw_json = line[5:].strip()
                            data = json.loads(raw_json)
                            # Extract tool result text
                            result_data = data.get("result", {})
                            content_list = result_data.get("content", [])
                            if content_list and "text" in content_list[0]:
                                parsed_text = content_list[0]["text"]
                                try:
                                    return json.loads(parsed_text)
                                except Exception:
                                    return {"text": parsed_text}
                            return result_data
                else:
                    logger.warning(f"Meko MCP returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Error querying Meko MCP ({tool_name}): {repr(e)}")

        return {}

    async def recall(
        self,
        datapack: str,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 5
    ) -> List[str]:
        """
        Recalls customer preferences or facts from Meko memory.
        """
        if not self.enabled or not self.api_key:
            return []

        datapack_id = self._resolve_datapack_id(datapack)
        cid = conversation_id or str(uuid.uuid4())

        args = {
            "query": query,
            "datapack_id": datapack_id,
            "conversation_id": cid,
            "limit": limit
        }

        result = await self._call_mcp_tool("memory_search", args, timeout=12.0)
        items: List[str] = []

        if isinstance(result, dict) and "results" in result:
            for item in result.get("results", []):
                mem_text = item.get("memory") or item.get("text")
                if mem_text:
                    items.append(str(mem_text))

        return items

    async def write(
        self,
        datapack: str,
        text: str,
        agent_id: str = "CustomerAgent",
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Stores an extracted fact into the specified Meko datapack.
        """
        if not self.enabled or not self.api_key:
            return {"status": "disabled"}

        datapack_id = self._resolve_datapack_id(datapack)
        cid = conversation_id or str(uuid.uuid4())

        args = {
            "text": text,
            "datapack_id": datapack_id,
            "conversation_id": cid,
            "agent_id": agent_id
        }
        if metadata:
            args["metadata"] = json.dumps(metadata)

        result = await self._call_mcp_tool("memory_add", args, timeout=5.0)
        return result

    async def promote(
        self,
        datapack: str,
        memory_id: str
    ) -> Dict[str, Any]:
        """
        Promotes a memory into shared business knowledge.
        """
        if not self.enabled or not self.api_key:
            return {"status": "disabled"}

        datapack_id = self._resolve_datapack_id(datapack)
        args = {
            "memory_ids": [memory_id],
            "datapack_id": datapack_id,
            "conversation_id": str(uuid.uuid4())
        }
        return await self._call_mcp_tool("memory_promote", args, timeout=5.0)


# Global singleton instance
_default_meko_adapter = None

def get_meko_adapter(enabled: bool = True) -> MekoAdapter:
    global _default_meko_adapter
    if _default_meko_adapter is None:
        _default_meko_adapter = MekoAdapter(enabled=enabled)
    return _default_meko_adapter
