import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
from backend.app.memory import MekoAdapter
from backend.app.models.schemas import ExtractedMessage, ConfidenceScore
from backend.app.agents.customer_agent import CustomerAgent

async def run_meko_tests():
    print("=== Testing Meko Long-Term Memory Integration (Phase 4) ===")

    # 1. Initialize Meko Adapter
    meko = MekoAdapter(enabled=True)
    customer_phone = "918587859710"

    # 2. Store customer preference in munim-customer datapack
    print("\n[1] Writing customer preference to munim-customer datapack...")
    write_res = await meko.write(
        datapack="customer",
        text=f"Customer {customer_phone} (Simran) previously ordered Cotton Anarkali Kurti in size XXL and Red color.",
        agent_id="CustomerAgent"
    )
    print("Write result:", write_res)

    # 3. Recall customer preference
    print("\n[2] Recalling customer memory from Meko...")
    memories = await meko.recall(
        datapack="customer",
        query=f"Customer {customer_phone} kurti size preference"
    )
    print(f"Recalled {len(memories)} memories:")
    for m in memories:
        print(" -", m)

    assert len(memories) > 0, "Expected at least 1 recalled memory from Meko"
    print("[PASS] Meko recall verified successfully")

    # 4. Demonstrate Meko ON vs OFF with Customer Agent
    print("\n[3] Testing Meko ON vs OFF demonstration...")

    query_msg = ExtractedMessage(
        message_id="msg-meko-test",
        customer_phone=customer_phone,
        customer_name="Simran",
        raw_text="Same wali kurti available hai kya?",
        type="catalog_query",
        confidence=ConfidenceScore(overall=0.90, items=0.90, amount=1.0)
    )

    # Scenario A: Meko OFF
    meko_off = MekoAdapter(enabled=False)
    agent_off = CustomerAgent(memory_engine=meko_off)
    res_off = await agent_off.handle(query_msg, context={"seller_id": "test_seller", "customer_id": customer_phone, "customer_name": "Simran"})
    print("\n🔴 Scenario A: Meko OFF Response:")
    print(res_off["reply"])

    # Scenario B: Meko ON
    agent_on = CustomerAgent(memory_engine=meko)
    res_on = await agent_on.handle(query_msg, context={"seller_id": "test_seller", "customer_id": customer_phone, "customer_name": "Simran"})
    print("\n🟢 Scenario B: Meko ON Response:")
    print(res_on["reply"])

    print("\nALL MEKO PHASE 4 TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_meko_tests())
