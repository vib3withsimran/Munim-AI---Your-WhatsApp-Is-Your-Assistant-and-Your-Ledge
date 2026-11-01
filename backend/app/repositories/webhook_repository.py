import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Union, Dict, Any
from uuid import UUID
from supabase import Client

from backend.app.core.config import settings
from backend.app.models.webhook import SellerWhatsAppChannel, WebhookMessage, WebhookProcessingStatus
from backend.app.schemas.webhook import normalize_whatsapp_phone
from backend.app.repositories.exceptions import (
    DuplicateRecordError,
    NotFoundError,
    RepositoryError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class WebhookRepository:
    """Data-access repository for WhatsApp channel mappings and distributed webhook idempotency."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def resolve_seller_by_phone(self, to_phone: str) -> Optional[str]:
        """
        Resolves tenant seller_id from the incoming Twilio destination ('To') number.
        Strictly enforces that inbound webhooks route to verified sellers.
        """
        normalized_to = normalize_whatsapp_phone(to_phone)
        if not normalized_to:
            return None

        # 1. Query database for registered active channel
        try:
            res = (
                self.db.table("seller_whatsapp_channels")
                .select("seller_id, is_active")
                .eq("phone_number", normalized_to)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
            if res and res.data:
                row = res.data[0] if isinstance(res.data, list) and res.data else res.data
                if isinstance(row, dict) and row.get("seller_id"):
                    return str(row["seller_id"])
        except Exception as e:
            logger.warning("Could not query seller_whatsapp_channels table: %s", e)

        # 2. In single-tenant/development environments, check fallback to configured TWILIO_WHATSAPP_NUMBER
        normalized_config = normalize_whatsapp_phone(settings.TWILIO_WHATSAPP_NUMBER)
        if normalized_to == normalized_config:
            # Check if an active seller exists in the system or fallback test seller
            fallback_seller = getattr(settings, "DEFAULT_SELLER_ID", None)
            if fallback_seller:
                return str(fallback_seller)

        return None

    def register_channel(
        self,
        seller_id: Union[str, UUID],
        phone_number: str,
        display_name: Optional[str] = None,
        is_active: bool = True,
    ) -> SellerWhatsAppChannel:
        """Registers a new WhatsApp channel number for a seller."""
        sid = self._normalize_id(seller_id)
        clean_phone = normalize_whatsapp_phone(phone_number)

        payload = {
            "seller_id": sid,
            "phone_number": clean_phone,
            "display_name": display_name,
            "is_active": is_active,
        }

        try:
            res = self.db.table("seller_whatsapp_channels").insert(payload).execute()
            if not res or not res.data:
                raise RepositoryError("Failed to register seller WhatsApp channel.")
            row = res.data[0] if isinstance(res.data, list) else res.data
            return SellerWhatsAppChannel.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="SellerWhatsAppChannel")

    def reserve_webhook_message(
        self,
        message_sid: str,
        from_phone: str,
        to_phone: str,
        seller_id: Optional[Union[str, UUID]] = None,
        media_type: str = "text",
        raw_text: Optional[str] = None,
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Atomically registers an incoming MessageSid in 'webhook_messages' table.
        Uses primary key constraint on message_sid as distributed idempotency lock.

        Returns:
            (is_new, record):
                - (True, new_row) if message was successfully claimed and marked 'processing'.
                - (False, existing_row) if message_sid already exists (retry or concurrent delivery).
        """
        clean_sid = message_sid.strip()
        norm_from = normalize_whatsapp_phone(from_phone)
        norm_to = normalize_whatsapp_phone(to_phone)
        sid_val = self._normalize_id(seller_id) if seller_id else None

        payload = {
            "message_sid": clean_sid,
            "seller_id": sid_val,
            "from_phone": norm_from,
            "to_phone": norm_to,
            "media_type": media_type or "text",
            "raw_text": raw_text,
            "processing_status": WebhookProcessingStatus.PROCESSING.value,
        }

        try:
            res = self.db.table("webhook_messages").insert(payload).execute()
            if res and res.data:
                row = res.data[0] if isinstance(res.data, list) else res.data
                return True, row
        except Exception as e:
            err_str = str(e).lower()
            if "23505" in err_str or "duplicate" in err_str or "conflict" in err_str or "primary key" in err_str:
                logger.info(f"MessageSid {clean_sid} already recorded. Fetching existing state.")
                # Fetch existing row
                try:
                    existing = (
                        self.db.table("webhook_messages")
                        .select("*")
                        .eq("message_sid", clean_sid)
                        .maybe_single()
                        .execute()
                    )
                    row = existing.data[0] if (existing and isinstance(existing.data, list) and existing.data) else (existing.data if existing else None)
                    return False, row
                except Exception as fetch_err:
                    logger.warning(f"Failed to fetch duplicate message {clean_sid}: {fetch_err}")
                    return False, {"message_sid": clean_sid, "processing_status": "duplicate"}
            logger.error(f"Error reserving webhook message {clean_sid}: {e}")
            raise map_supabase_error(e, entity="WebhookMessage")

        return False, None

    def mark_message_completed(
        self,
        message_sid: str,
        intent: Optional[str] = None,
        response_summary: Optional[str] = None,
    ) -> bool:
        """Marks a message as successfully processed and records the response summary."""
        clean_sid = message_sid.strip()
        update_data = {
            "processing_status": WebhookProcessingStatus.COMPLETED.value,
            "intent": intent,
            "response_summary": response_summary,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self.db.table("webhook_messages").update(update_data).eq("message_sid", clean_sid).execute()
            return True
        except Exception as e:
            logger.warning(f"Could not update webhook message {clean_sid} to completed: {e}")
            return False

    def mark_message_failed(
        self,
        message_sid: str,
        error_message: str,
    ) -> bool:
        """Marks a message as failed with error details."""
        clean_sid = message_sid.strip()
        update_data = {
            "processing_status": WebhookProcessingStatus.FAILED.value,
            "error_message": error_message[:500] if error_message else "Unknown error",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self.db.table("webhook_messages").update(update_data).eq("message_sid", clean_sid).execute()
            return True
        except Exception as e:
            logger.warning(f"Could not update webhook message {clean_sid} to failed: {e}")
            return False

    def mark_message_quarantined(
        self,
        message_sid: str,
        from_phone: str,
        to_phone: str,
        reason: str,
        raw_text: Optional[str] = None,
    ) -> bool:
        """Quarantines unroutable or untrusted messages."""
        clean_sid = message_sid.strip()
        norm_from = normalize_whatsapp_phone(from_phone)
        norm_to = normalize_whatsapp_phone(to_phone)

        payload = {
            "message_sid": clean_sid,
            "seller_id": None,
            "from_phone": norm_from,
            "to_phone": norm_to,
            "media_type": "text",
            "raw_text": raw_text,
            "processing_status": WebhookProcessingStatus.QUARANTINED.value,
            "error_message": reason,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Try insert first; if exists, update
            self.db.table("webhook_messages").upsert(payload).execute()
            return True
        except Exception as e:
            logger.warning(f"Could not quarantine message {clean_sid}: {e}")
            return False

    def get_message_status(self, message_sid: str) -> Optional[Dict[str, Any]]:
        """Retrieves processing status and details for a message_sid."""
        clean_sid = message_sid.strip()
        try:
            res = (
                self.db.table("webhook_messages")
                .select("*")
                .eq("message_sid", clean_sid)
                .maybe_single()
                .execute()
            )
            if res and res.data:
                row = res.data[0] if isinstance(res.data, list) and res.data else res.data
                return row
            return None
        except Exception as e:
            logger.warning(f"Error fetching message status for {clean_sid}: {e}")
            return None

