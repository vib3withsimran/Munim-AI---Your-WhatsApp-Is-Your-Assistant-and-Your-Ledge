import sqlite3
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from backend.app.services.db import get_db_path
from backend.app.queue.models import QueueJob, JobStatus

logger = logging.getLogger(__name__)

class DurableQueue:
    """
    SQLite-backed durable queue for asynchronous background jobs.
    Ensures zero message loss across application restarts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_db_path()
        self._is_mem = (self.db_path == ":memory:")
        self._mem_conn = sqlite3.connect(":memory:", timeout=10.0) if self._is_mem else None
        if self._mem_conn:
            self._mem_conn.row_factory = sqlite3.Row
        self._init_table()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_mem and self._mem_conn:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _close_connection(self, conn: sqlite3.Connection):
        if not self._is_mem:
            conn.close()

    def _init_table(self):
        """Creates the queue_jobs table if it does not already exist."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS queue_jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_queue_status ON queue_jobs(status, created_at);")
        finally:
            self._close_connection(conn)

    def enqueue(self, job_type: str, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """
        Adds a new job to the queue. Returns the unique job ID.
        """
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload)

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO queue_jobs (id, job_type, payload, status, attempts, max_retries, last_error, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, NULL, ?, ?)
                    """,
                    (job_id, job_type, payload_json, JobStatus.PENDING, max_retries, now, now)
                )
            logger.info(f"Enqueued job {job_id} [{job_type}]")
            return job_id
        finally:
            self._close_connection(conn)

    def dequeue(self) -> Optional[QueueJob]:
        """
        Atomically fetches the next available pending job and marks it as processing.
        """
        conn = self._get_connection()
        try:
            with conn:
                # Find oldest pending job or retrying job
                cursor = conn.execute(
                    """
                    SELECT * FROM queue_jobs
                    WHERE status IN (?, ?)
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (JobStatus.PENDING, JobStatus.RETRYING)
                )
                row = cursor.fetchone()
                if not row:
                    return None

                job_id = row["id"]
                attempts = row["attempts"] + 1
                now = datetime.now(timezone.utc).isoformat()

                # Atomically mark as processing
                conn.execute(
                    """
                    UPDATE queue_jobs
                    SET status = ?, attempts = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (JobStatus.PROCESSING, attempts, now, job_id)
                )

                payload = json.loads(row["payload"])
                return QueueJob(
                    id=row["id"],
                    job_type=row["job_type"],
                    payload=payload,
                    status=JobStatus.PROCESSING,
                    attempts=attempts,
                    max_retries=row["max_retries"],
                    last_error=row["last_error"],
                    created_at=row["created_at"],
                    updated_at=now
                )
        finally:
            self._close_connection(conn)

    def mark_completed(self, job_id: str, result_meta: Optional[Dict[str, Any]] = None):
        """Marks a job as completed."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "UPDATE queue_jobs SET status = ?, updated_at = ? WHERE id = ?",
                    (JobStatus.COMPLETED, now, job_id)
                )
            logger.info(f"Job {job_id} marked as COMPLETED.")
        finally:
            self._close_connection(conn)

    def mark_failed(self, job_id: str, error_msg: str, allow_retry: bool = True):
        """Marks a job as failed or schedules retry if attempts < max_retries."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("SELECT attempts, max_retries FROM queue_jobs WHERE id = ?", (job_id,))
                row = cursor.fetchone()
                if not row:
                    return

                attempts = row["attempts"]
                max_retries = row["max_retries"]

                new_status = JobStatus.RETRYING if (allow_retry and attempts < max_retries) else JobStatus.FAILED

                conn.execute(
                    "UPDATE queue_jobs SET status = ?, last_error = ?, updated_at = ? WHERE id = ?",
                    (new_status, error_msg[:500], now, job_id)
                )
            logger.warning(f"Job {job_id} marked as {new_status}: {error_msg}")
        finally:
            self._close_connection(conn)

    def get_stats(self) -> Dict[str, int]:
        """Returns counts of jobs by status."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT status, count(*) as count FROM queue_jobs GROUP BY status")
            counts = {row["status"]: row["count"] for row in cursor.fetchall()}
            return {
                "pending": counts.get(JobStatus.PENDING, 0),
                "processing": counts.get(JobStatus.PROCESSING, 0),
                "completed": counts.get(JobStatus.COMPLETED, 0),
                "failed": counts.get(JobStatus.FAILED, 0),
                "retrying": counts.get(JobStatus.RETRYING, 0),
                "total": sum(counts.values())
            }
        finally:
            self._close_connection(conn)

    def get_recent_jobs(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recent jobs for monitoring / dashboard."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM queue_jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            jobs = []
            for row in cursor.fetchall():
                try:
                    payload = json.loads(row["payload"])
                except Exception:
                    payload = {}
                jobs.append({
                    "id": row["id"],
                    "job_type": row["job_type"],
                    "payload": payload,
                    "status": row["status"],
                    "attempts": row["attempts"],
                    "max_retries": row["max_retries"],
                    "last_error": row["last_error"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            return jobs
        finally:
            self._close_connection(conn)

    def retry_all_failed(self) -> int:
        """Resets all failed jobs back to pending."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE queue_jobs SET status = ?, attempts = 0, updated_at = ? WHERE status = ?",
                    (JobStatus.PENDING, now, JobStatus.FAILED)
                )
                count = cursor.rowcount
            logger.info(f"Reset {count} failed jobs back to PENDING.")
            return count
        finally:
            self._close_connection(conn)


# Global Singleton Queue Instance
_default_queue = None

def get_queue() -> DurableQueue:
    global _default_queue
    if _default_queue is None:
        _default_queue = DurableQueue()
    return _default_queue
