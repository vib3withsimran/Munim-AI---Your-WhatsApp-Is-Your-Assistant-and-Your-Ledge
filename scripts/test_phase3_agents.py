import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import asyncio
from backend.app.models.schemas import ExtractedMessage, OrderItem, ConfidenceScore
from backend.app.agents import CustomerAgent, OrderAgent, FinanceAgent, Orchestrator

async def run_agent_tests():
    print("=== Testing Phase 3: Orchestrator & Three Agents ===")

    # Setup Agents
    orchestrator = Orchestrator()
    customer_agent = CustomerAgent()
    order_agent = OrderAgent()
    finance_agent = FinanceAgent()

    test_seller_uuid = str(uuid.uuid4())
    test_customer_uuid = str(uuid.uuid4())

    context = {
        "seller_id": test_seller_uuid,
        "customer_id": test_customer_uuid,
        "customer_name": "Simran"
    }

    # -------------------------------------------------------------
    # 1. Test Customer Agent (Catalog search & inquiry)
    # -------------------------------------------------------------
    cat_msg = ExtractedMessage(
        message_id="msg-cat-1",
        customer_phone="919876543210",
        raw_text="Aapke paas anarkali available hai kya xxl size mein?",
        type="catalog_query",
        confidence=ConfidenceScore(overall=0.95, items=0.95, amount=1.0)
    )
    res_cat = await customer_agent.handle(cat_msg, context)
    assert res_cat["agent"] == "CustomerAgent"
    assert res_cat["action"] == "catalog_replied"
    assert "Cotton Anarkali Kurti" in res_cat["reply"]
    print("[PASS] CustomerAgent catalog query handled successfully")

    # -------------------------------------------------------------
    # 2. Test Order Agent (Stock reservation & Order creation)
    # -------------------------------------------------------------
    order_msg = ExtractedMessage(
        message_id="msg-ord-1",
        customer_phone="919876543210",
        raw_text="2 anarkali kurti bhej do",
        type="order",
        items=[
            OrderItem(name="Cotton Anarkali Kurti", qty=2, size="XXL", unit_price=1299.0)
        ],
        amount=2598.0,
        confidence=ConfidenceScore(overall=0.95, items=0.95, amount=0.95)
    )
    res_ord = await order_agent.handle(order_msg, context)
    assert res_ord["agent"] == "OrderAgent"
    assert res_ord["action"] == "order_created"
    assert "ORD-" in res_ord["reply"]
    assert res_ord["data"]["total_amount"] == 2598.0
    print("[PASS] OrderAgent created order with deterministic math: total=₹2,598")

    created_order_id = res_ord["data"]["order_id"]

    # -------------------------------------------------------------
    # 3. Test Finance Agent (UPI screenshot & Payment Claim)
    # -------------------------------------------------------------
    pay_msg = ExtractedMessage(
        message_id="msg-pay-1",
        customer_phone="919876543210",
        raw_text="Payment of ₹2598 done via PhonePe",
        media_type="image",
        type="payment",
        amount=2598.0,
        upi_txn_id="409281726351",
        linked_order_id=created_order_id,
        confidence=ConfidenceScore(overall=0.98, items=1.0, amount=0.98)
    )
    res_pay = await finance_agent.handle(pay_msg, context)
    assert res_pay["agent"] == "FinanceAgent"
    assert res_pay["action"] == "payment_claim_created"
    assert "PAY-" in res_pay["data"]["claim"]["payment_id"]
    assert res_pay["data"]["claim"]["claim_status"] == "pending_verification"
    print("[PASS] FinanceAgent recorded payment claim: pending_verification")

    # -------------------------------------------------------------
    # 4. Test Orchestrator (Deterministic Rules & Routing)
    # -------------------------------------------------------------
    # A. Privacy switch #private
    priv_msg = ExtractedMessage(
        message_id="msg-priv-1",
        customer_phone="919876543210",
        raw_text="#private",
        type="command"
    )
    res_priv = await orchestrator.route_and_execute(priv_msg, context)
    assert res_priv["action"] == "privacy_activated"
    assert "Munim AI Paused" in res_priv["reply"]
    print("[PASS] Orchestrator handled #private switch deterministically")

    # B. Privacy resume #resume
    res_msg = ExtractedMessage(
        message_id="msg-res-1",
        customer_phone="919876543210",
        raw_text="#resume",
        type="command"
    )
    res_resume = await orchestrator.route_and_execute(res_msg, context)
    assert res_resume["action"] == "privacy_deactivated"
    print("[PASS] Orchestrator handled #resume switch deterministically")

    # C. Intent routing to Order Agent
    orch_ord = await orchestrator.route_and_execute(order_msg, context)
    assert orch_ord["agent_used"] == "OrderAgent"
    assert orch_ord["action"] == "order_created"
    print("[PASS] Orchestrator routed order intent to OrderAgent")

    # D. Intent routing to Finance Agent
    orch_pay = await orchestrator.route_and_execute(pay_msg, context)
    assert orch_pay["agent_used"] == "FinanceAgent"
    assert orch_pay["action"] == "payment_claim_created"
    print("[PASS] Orchestrator routed payment intent to FinanceAgent")

    # E. Owner Command (summary)
    sum_msg = ExtractedMessage(
        message_id="msg-sum-1",
        customer_phone="919876543210",
        raw_text="summary",
        type="command"
    )
    res_sum = await orchestrator.route_and_execute(sum_msg, context)
    assert res_sum["agent_used"] == "FinanceAgent"
    assert "Daily Financial Summary" in res_sum["reply"]
    print("[PASS] Orchestrator routed summary command deterministically")

    print("\nALL PHASE 3 AGENT & ORCHESTRATOR TESTS PASSED!")

if __name__ == "__main__":
    asyncio.run(run_agent_tests())
