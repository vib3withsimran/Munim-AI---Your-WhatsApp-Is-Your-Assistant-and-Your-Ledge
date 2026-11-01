import asyncio
import logging
from typing import Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.queue import get_queue, JobType, QueueJob
from backend.app.services.whatsapp import send_whatsapp_message
from backend.app.services.database_service import get_active_seller_id, get_or_create_customer_uuid

logger = logging.getLogger(__name__)

class QueueWorker:
    """
    Asynchronous background queue worker.
    Processes queued jobs (outbound WhatsApp messages, payment alerts, heavy message jobs)
    completely decoupled from the fast HTTP webhook cycle.
    """

    def __init__(self, queue=None, poll_interval: float = 1.0):
        self.queue = queue or get_queue()
        self.poll_interval = poll_interval
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def process_job(self, job: QueueJob) -> bool:
        """
        Executes a single queue job based on its job_type.
        Returns True if successful, False if failed.
        """
        job_type = job.job_type
        payload = job.payload
        logger.info(f"Worker processing job {job.id} [{job_type}] (attempt {job.attempts})")

        try:
            if job_type == JobType.OUTBOUND_WHATSAPP:
                to_phone = payload.get("to_phone", "")
                text = payload.get("text", "")
                if not to_phone or not text:
                    raise ValueError("Missing 'to_phone' or 'text' in OUTBOUND_WHATSAPP payload.")
                
                res = await send_whatsapp_message(to_phone=to_phone, text=text)
                if isinstance(res, dict) and "error" in res:
                    raise RuntimeError(f"Twilio delivery failed: {res['error']}")
                self.queue.mark_completed(job.id, res)
                return True

            elif job_type == JobType.PAYMENT_APPROVED_ALERT:
                to_phone = payload.get("to_phone", "")
                order_id = payload.get("order_id", "")
                amount = payload.get("amount", "")
                customer_name = payload.get("customer_name") or "Ji"

                alert_text = (
                    f"Namaste {customer_name}! 🙏\n\n"
                    f"Aapki ₹{int(float(amount or 0))} ki payment verify aur confirm kar li gayi hai! ✅\n"
                    f"Aapka order *{order_id}* packing aur dispatch ke liye schedule ho chuka hai.\n\n"
                    f"Tracking details jald hi WhatsApp par share kar di jayengi. Dhanyawaad!"
                )
                res = await send_whatsapp_message(to_phone=to_phone, text=alert_text)
                self.queue.mark_completed(job.id, res)
                return True

            elif job_type == JobType.DAILY_DUES_DIGEST:
                seller_id = payload.get("seller_id") or get_active_seller_id()
                to_phone = payload.get("to_phone") or settings.OWNER_WHATSAPP_NUMBER
                
                from backend.app.agents.finance_agent import FinanceAgent
                finance_agent = FinanceAgent()
                summary_text = await finance_agent.get_summary_report(seller_id)
                
                digest_msg = f"📊 *Munim AI Daily Business Digest*\n\n{summary_text}"
                res = await send_whatsapp_message(to_phone=to_phone, text=digest_msg)
                self.queue.mark_completed(job.id, res)
                return True

            elif job_type == JobType.INCOMING_HEAVY_MESSAGE:
                sender_phone = payload.get("sender_phone", "")
                contact_name = payload.get("contact_name", "")
                raw_text = payload.get("raw_text", "")
                msg_type = payload.get("msg_type", "text")
                media_url = payload.get("media_url", "")
                media_content_type = payload.get("media_content_type", "")
                message_id = payload.get("message_id", "")
                timestamp = payload.get("timestamp", "")

                from backend.app.ai import extract_text, extract_audio, extract_image
                from backend.app.agents import Orchestrator

                extracted = None
                # Media fetch if applicable
                if media_url and (msg_type in ["image", "audio"]):
                    from backend.app.api.routes.webhook import fetch_twilio_media
                    media_bytes = await fetch_twilio_media(media_url)
                    if media_bytes:
                        if msg_type == "image":
                            extracted = await extract_image(
                                image_bytes=media_bytes,
                                mime_type=media_content_type or "image/jpeg",
                                customer_phone=sender_phone,
                                message_id=message_id,
                                timestamp=timestamp
                            )
                        elif msg_type == "audio":
                            extracted = await extract_audio(
                                audio_bytes=media_bytes,
                                mime_type=media_content_type or "audio/ogg",
                                customer_phone=sender_phone,
                                message_id=message_id,
                                timestamp=timestamp
                            )

                if not extracted:
                    extracted = await extract_text(
                        raw_text=raw_text or "[Empty message]",
                        customer_phone=sender_phone,
                        message_id=message_id,
                        timestamp=timestamp
                    )

                seller_uuid = get_active_seller_id()
                customer_uuid = get_or_create_customer_uuid(seller_uuid, sender_phone, contact_name)
                context = {
                    "seller_id": seller_uuid,
                    "customer_id": customer_uuid,
                    "customer_phone": sender_phone,
                    "customer_name": contact_name or extracted.customer_name or "Ji"
                }

                orchestrator = Orchestrator()
                result = await orchestrator.route_and_execute(extracted, context)
                reply_text = result.get("reply", "")

                if reply_text:
                    await send_whatsapp_message(to_phone=sender_phone, text=reply_text)

                self.queue.mark_completed(job.id, {"agent_used": result.get("agent_used")})
                return True

            else:
                raise ValueError(f"Unknown job type '{job_type}'")

        except Exception as e:
            logger.error(f"Error executing job {job.id} ({job_type}): {e}", exc_info=True)
            self.queue.mark_failed(job.id, str(e), allow_retry=True)
            return False

    async def run_once(self) -> bool:
        """
        Processes next pending job from the queue.
        Returns True if a job was processed, False if queue was empty.
        """
        job = self.queue.dequeue()
        if not job:
            return False
        await self.process_job(job)
        return True

    async def _worker_loop(self):
        """Continuous polling loop."""
        logger.info("Async QueueWorker background loop started.")
        while self._is_running:
            try:
                processed = await self.run_once()
                if not processed:
                    await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
        logger.info("Async QueueWorker background loop stopped.")

    def start(self):
        """Starts the worker loop in the current asyncio event loop."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._worker_loop())

    async def stop(self):
        """Gracefully stops the worker loop."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# Global Singleton Worker Instance
_default_worker = None

def get_queue_worker() -> QueueWorker:
    global _default_worker
    if _default_worker is None:
        _default_worker = QueueWorker()
    return _default_worker

