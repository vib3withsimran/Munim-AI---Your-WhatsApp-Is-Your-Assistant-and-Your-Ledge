from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class JobType:
    INCOMING_HEAVY_MESSAGE = "INCOMING_HEAVY_MESSAGE"
    OUTBOUND_WHATSAPP = "OUTBOUND_WHATSAPP"
    PAYMENT_APPROVED_ALERT = "PAYMENT_APPROVED_ALERT"
    DAILY_DUES_DIGEST = "DAILY_DUES_DIGEST"

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class QueueJob:
    id: str
    job_type: str
    payload: Dict[str, Any]
    status: str = JobStatus.PENDING
    attempts: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_type": self.job_type,
            "payload": self.payload,
            "status": self.status,
            "attempts": self.attempts,
            "max_retries": self.max_retries,
            "last_error": self.last_error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
