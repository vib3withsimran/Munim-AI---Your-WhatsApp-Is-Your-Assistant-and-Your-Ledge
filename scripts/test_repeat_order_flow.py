import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.ai.text_extractor import extract_text
from backend.app.agents.orchestrator import Orchestrator

async def main():
    print("=== Testing Repeat Order Flow with Meko Long-Term Memory ===")
    
    orch = Orchestrator()
    sender_phone = "918587859710"
    raw_message = "Meine phle jo order kara tha vahi vaapis karna ha same quantity and all"
    
    print(f"\nIncoming Message: '{raw_message}'")
    
    t0 = time.time()
    extracted = await extract_text(raw_message, sender_phone)
    t1 = time.time()
    
    print(f"\n[1] Intent Extraction ({round(t1 - t0, 3)}s):")
    print(f"    Type: {extracted.type}")
    print(f"    Confidence: {extracted.confidence.overall}")
    print(f"    Items detected in text: {len(extracted.items)}")
    
    context = {
        "seller_id": "00000000-0000-0000-0000-000000000001",
        "customer_id": "00000000-0000-0000-0000-000000000002",
        "customer_phone": sender_phone,
        "customer_name": "Simran"
    }
    
    t2 = time.time()
    result = await orch.route_and_execute(extracted, context)
    t3 = time.time()
    
    print(f"\n[2] Agent Execution ({round(t3 - t2, 3)}s):")
    print(f"    Agent Used: {result.get('agent_used')}")
    print(f"    Action: {result.get('action')}")
    print(f"\n[3] Delivered Reply:\n----------------------------------------")
    print(result.get("reply", ""))
    print("----------------------------------------")
    print(f"\nTotal Pipeline Latency: {round(t3 - t0, 3)}s")

if __name__ == "__main__":
    asyncio.run(main())
