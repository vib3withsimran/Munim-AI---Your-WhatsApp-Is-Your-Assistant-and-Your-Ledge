import pytest
import os
import tempfile
import asyncio
from unittest.mock import patch, AsyncMock

from backend.app.queue.models import QueueJob, JobType, JobStatus
from backend.app.queue.durable_queue import DurableQueue
from backend.app.workers.queue_worker import QueueWorker

@pytest.fixture
def temp_queue():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name
    queue = DurableQueue(db_path=temp_path)
    yield queue
    try:
        os.remove(temp_path)
    except Exception:
        pass

def test_enqueue_and_dequeue(temp_queue):
    job_id = temp_queue.enqueue(
        job_type=JobType.OUTBOUND_WHATSAPP,
        payload={"to_phone": "918587859710", "text": "Test message"}
    )
    assert job_id.startswith("job-")

    stats = temp_queue.get_stats()
    assert stats["pending"] == 1
    assert stats["total"] == 1

    job = temp_queue.dequeue()
    assert job is not None
    assert job.id == job_id
    assert job.status == JobStatus.PROCESSING
    assert job.attempts == 1
    assert job.payload["to_phone"] == "918587859710"

    # Queue should now have 0 pending and 1 processing
    stats = temp_queue.get_stats()
    assert stats["pending"] == 0
    assert stats["processing"] == 1

    # Mark completed
    temp_queue.mark_completed(job.id)
    stats = temp_queue.get_stats()
    assert stats["processing"] == 0
    assert stats["completed"] == 1

def test_job_retry_and_failure(temp_queue):
    job_id = temp_queue.enqueue(
        job_type=JobType.OUTBOUND_WHATSAPP,
        payload={"to_phone": "918587859710", "text": "Fail test"},
        max_retries=2
    )

    # First attempt fails -> should be retrying
    job1 = temp_queue.dequeue()
    assert job1 is not None
    temp_queue.mark_failed(job1.id, "Network timeout 1", allow_retry=True)

    stats = temp_queue.get_stats()
    assert stats["retrying"] == 1

    # Second attempt (attempts reaches max_retries=2)
    job2 = temp_queue.dequeue()
    assert job2 is not None
    assert job2.attempts == 2
    temp_queue.mark_failed(job2.id, "Network timeout 2", allow_retry=True)

    stats = temp_queue.get_stats()
    assert stats["retrying"] == 0
    assert stats["failed"] == 1

    # Retry all failed
    requeued = temp_queue.retry_all_failed()
    assert requeued == 1
    assert temp_queue.get_stats()["pending"] == 1

def test_worker_process_outbound_whatsapp(temp_queue):
    async def _run():
        job_id = temp_queue.enqueue(
            job_type=JobType.OUTBOUND_WHATSAPP,
            payload={"to_phone": "918587859710", "text": "Namaste!"}
        )

        worker = QueueWorker(queue=temp_queue)
        with patch("backend.app.workers.queue_worker.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sid": "SM_MOCK_123"}
            processed = await worker.run_once()
            assert processed is True
            mock_send.assert_awaited_once_with(to_phone="918587859710", text="Namaste!")

        stats = temp_queue.get_stats()
        assert stats["completed"] == 1
    asyncio.run(_run())


def test_worker_process_payment_alert(temp_queue):
    async def _run():
        job_id = temp_queue.enqueue(
            job_type=JobType.PAYMENT_APPROVED_ALERT,
            payload={
                "to_phone": "918587859710",
                "order_id": "ORD-12345",
                "amount": "1299",
                "customer_name": "Simran"
            }
        )

        worker = QueueWorker(queue=temp_queue)
        with patch("backend.app.workers.queue_worker.send_whatsapp_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sid": "SM_MOCK_456"}
            processed = await worker.run_once()
            assert processed is True
            mock_send.assert_awaited_once()
            args = mock_send.call_args[1]
            assert "ORD-12345" in args["text"]
            assert "1299" in args["text"]

        stats = temp_queue.get_stats()
        assert stats["completed"] == 1
    asyncio.run(_run())


def test_worker_lifecycle(temp_queue):
    async def _run():
        worker = QueueWorker(queue=temp_queue, poll_interval=0.05)
        worker.start()
        assert worker._is_running is True
        await asyncio.sleep(0.1)
        await worker.stop()
        assert worker._is_running is False
    asyncio.run(_run())


def test_queue_api_endpoints():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client = TestClient(app)

    # 1. Test status
    res = client.get("/queue/status")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "pending" in data["metrics"]

    # 2. Test enqueue
    res_enq = client.post(
        "/queue/enqueue",
        json={
            "job_type": "OUTBOUND_WHATSAPP",
            "payload": {"to_phone": "918587859710", "text": "Hello API queue"},
            "max_retries": 3
        }
    )
    assert res_enq.status_code == 201
    job_id = res_enq.json()["job_id"]
    assert job_id.startswith("job-")

    # 3. Test list jobs
    res_jobs = client.get("/queue/jobs?limit=5")
    assert res_jobs.status_code == 200
    assert res_jobs.json()["count"] >= 1

    # 4. Test retry failed
    res_retry = client.post("/queue/retry-failed")
    assert res_retry.status_code == 200
    assert "requeued_count" in res_retry.json()
