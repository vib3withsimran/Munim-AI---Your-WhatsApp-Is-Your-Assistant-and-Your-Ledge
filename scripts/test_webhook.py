import os
import sys
import uuid
import asyncio
import httpx

sys.stdout.reconfigure(encoding="utf-8")

# Ensure DRY_RUN is enabled for testing
os.environ["DRY_RUN"] = "1"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

def make_twilio_payload(body: str, phone: str = "919876543210", name: str = "Priya Sharma", msg_id: str = None) -> dict:
    if not msg_id:
        msg_id = f"SM{uuid.uuid4().hex[:16]}"
    return {
        "MessageSid": msg_id,
        "From": f"whatsapp:+{phone}",
        "To": "whatsapp:+14155238886",
        "ProfileName": name,
        "Body": body,
        "NumMedia": "0"
    }

async def run_tests():
    print("=" * 65)
    print("🧪 MUNIM AI — WEBHOOK TEST SUITE (TWILIO & FAST-PATH VERIFICATION)")
    print("=" * 65)

    # Use httpx.AsyncClient with ASGI app directly (no need to open external port)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        
        # Test 1: Catalog Query (Twilio Form payload)
        print("\n🔹 TEST 1: Twilio Form Catalog Query ('Pink anarkali abhi bhi available ha kya')")
        p1 = make_twilio_payload("Pink anarkali abhi bhi available ha kya", phone="919876543210", name="Priya")
        r1 = await client.post("/webhook", data=p1)
        print(f"HTTP Status: {r1.status_code}")
        print(f"TwiML Response:\n{r1.text.strip()}")

        # Test 2: Order Placement (Twilio Form payload)
        print("\n🔹 TEST 2: Twilio Form Order Placement ('Didi 2 anarkali kurti medium chahiye pink wali')")
        p2 = make_twilio_payload("Didi 2 anarkali kurti medium chahiye pink wali", phone="919876543210", name="Priya")
        r2 = await client.post("/webhook", data=p2)
        print(f"HTTP Status: {r2.status_code}")
        print(f"TwiML Response:\n{r2.text.strip()}")

        # Test 3: Discount / Ambiguity (Owner Escalation)
        print("\n🔹 TEST 3: Discount Request ('20% discount milega kya?') -> Should Escalate to Owner")
        p3 = make_twilio_payload("20% discount milega kya?", phone="919876543210", name="Priya")
        r3 = await client.post("/webhook", data=p3)
        print(f"HTTP Status: {r3.status_code}")
        print(f"TwiML Response:\n{r3.text.strip()}")

        # Test 4: Payment Confirmation
        print("\n🔹 TEST 4: Payment Confirmation ('Maine 1198 UPI kar diya check karo')")
        p4 = make_twilio_payload("Maine 1198 UPI kar diya check karo", phone="919876543210", name="Priya")
        r4 = await client.post("/webhook", data=p4)
        print(f"HTTP Status: {r4.status_code}")
        print(f"TwiML Response:\n{r4.text.strip()}")

        # Test 5: Duplicate Webhook Protection
        print("\n🔹 TEST 5: Duplicate Message Protection (Re-sending exact same message ID)")
        duplicate_id = f"SM_fixed_{uuid.uuid4().hex[:8]}"
        p5 = make_twilio_payload("Hello duplicate test", msg_id=duplicate_id)
        
        r5_first = await client.post("/webhook", data=p5)
        print(f"First attempt: {r5_first.status_code}")
        
        r5_second = await client.post("/webhook", data=p5)
        print(f"Second attempt (Retry): {r5_second.status_code} ({r5_second.text})")

    print("\n" + "=" * 65)
    print("✅ WEBHOOK TEST SUITE COMPLETE!")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_tests())
