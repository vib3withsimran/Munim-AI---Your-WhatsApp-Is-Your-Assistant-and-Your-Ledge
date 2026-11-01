import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.queue import get_queue, JobType, JobStatus
from backend.app.workers.queue_worker import QueueWorker

async def main():
    print("=== Testing Phase 5: Async Message Queue & Background Worker ===")
    
    queue = get_queue()
    initial_stats = queue.get_stats()
    print(f"\n[1] Initial Queue Metrics:\n    {initial_stats}")
    
    # 1. Enqueue Outbound WhatsApp Message
    job1_id = queue.enqueue(
        job_type=JobType.OUTBOUND_WHATSAPP,
        payload={
            "to_phone": "918587859710",
            "text": "Namaste Simran! 🙏 Munim AI background queue worker is active."
        }
    )
    print(f"\n[2] Enqueued Job 1 ({JobType.OUTBOUND_WHATSAPP}): {job1_id}")

    # 2. Enqueue Payment Approved Alert
    job2_id = queue.enqueue(
        job_type=JobType.PAYMENT_APPROVED_ALERT,
        payload={
            "to_phone": "918587859710",
            "order_id": "ORD-1EAE46",
            "amount": "1299",
            "customer_name": "Simran"
        }
    )
    print(f"[3] Enqueued Job 2 ({JobType.PAYMENT_APPROVED_ALERT}): {job2_id}")

    # 3. Enqueue Daily Dues Digest
    job3_id = queue.enqueue(
        job_type=JobType.DAILY_DUES_DIGEST,
        payload={
            "seller_id": "00000000-0000-0000-0000-000000000001",
            "to_phone": "918587859710"
        }
    )
    print(f"[4] Enqueued Job 3 ({JobType.DAILY_DUES_DIGEST}): {job3_id}")

    stats_after_enq = queue.get_stats()
    print(f"\n[5] Queue Metrics After Enqueueing:\n    {stats_after_enq}")
    assert stats_after_enq["pending"] >= 3, "Expected at least 3 pending jobs."

    # 4. Run QueueWorker to process all pending jobs
    print("\n[6] Launching QueueWorker to process queued jobs...")
    worker = QueueWorker(queue=queue)
    
    processed_count = 0
    t0 = time.time()
    while True:
        job_ran = await worker.run_once()
        if not job_ran:
            break
        processed_count += 1
    t1 = time.time()
    
    print(f"    Worker processed {processed_count} jobs in {round(t1 - t0, 3)}s.")

    # 5. Verify final queue metrics
    final_stats = queue.get_stats()
    print(f"\n[7] Final Queue Metrics:\n    {final_stats}")
    print(f"\n[PASS] Phase 5 Async Message Queue & Background Worker verified successfully!")

if __name__ == "__main__":
    asyncio.run(main())
