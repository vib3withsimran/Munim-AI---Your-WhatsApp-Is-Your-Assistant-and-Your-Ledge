import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, status

from backend.app.queue import get_queue, JobType

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/queue", tags=["Message Queue"])

class EnqueueRequest(BaseModel):
    job_type: str = Field(description="Job type: OUTBOUND_WHATSAPP, PAYMENT_APPROVED_ALERT, DAILY_DUES_DIGEST, INCOMING_HEAVY_MESSAGE")
    payload: Dict[str, Any] = Field(description="Job payload dictionary")
    max_retries: int = Field(default=3, ge=1, le=10)

@router.get("/status")
async def get_queue_status():
    """Returns real-time queue metrics: pending, processing, completed, failed counts."""
    queue = get_queue()
    stats = queue.get_stats()
    return {
        "status": "online",
        "metrics": stats
    }

@router.get("/jobs")
async def list_recent_jobs(limit: int = Query(default=15, ge=1, le=50)):
    """Lists recent queue jobs for monitoring."""
    queue = get_queue()
    jobs = queue.get_recent_jobs(limit=limit)
    return {
        "count": len(jobs),
        "jobs": jobs
    }

@router.post("/retry-failed")
async def retry_failed_jobs():
    """Resets all failed jobs to PENDING to trigger worker retry."""
    queue = get_queue()
    requeued_count = queue.retry_all_failed()
    return {
        "status": "success",
        "requeued_count": requeued_count
    }

@router.post("/enqueue", status_code=status.HTTP_201_CREATED)
async def enqueue_custom_job(req: EnqueueRequest):
    """Enqueues a new background job."""
    queue = get_queue()
    job_id = queue.enqueue(
        job_type=req.job_type,
        payload=req.payload,
        max_retries=req.max_retries
    )
    return {
        "status": "enqueued",
        "job_id": job_id
    }
