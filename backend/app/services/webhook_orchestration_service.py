import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Mapping, Optional, Tuple, Union
from uuid import UUID

import httpx
from fastapi import HTTPException, Response, status
from supabase import Client

from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase_client
from backend.app.models.webhook import WebhookProcessingStatus
from backend.app.schemas.customer import CustomerCreateRequest
from backend.app.schemas.order import OrderCreateRequest, OrderItemCreateRequest
from backend.app.schemas.payment import PaymentCreateRequest, PaymentMethod, PaymentStatus
from backend.app.schemas.webhook import IncomingTwilioPayload, normalize_whatsapp_phone
from backend.app.utils.twilio_auth import validate_twilio_signature
from backend.app.utils.privacy import check_privacy, set_customer_privacy, is_customer_private_in_db
from backend.app.repositories.webhook_repository import WebhookRepository
from backend.app.repositories.privacy_repository import PrivacyRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.product_service import ProductService
from backend.app.services.order_service import OrderService
from backend.app.services.payment_service import PaymentService
from backend.app.services.storage_service import StorageService
from backend.app.services.dashboard_service import get_dashboard_summary
from backend.app.services.sheets import get_store_summary
from backend.app.ai import extract_text, extract_audio, extract_image
from backend.app.agents import Orchestrator

logger = logging.getLogger(__name__)

FAST_GREETINGS = {
    "hi", "hii", "hiiii", "hello", "hello ji", "hey", "heyy",
    "namaste", "namaste ji", "pranam",
    "kaise ho", "kaise ho aap", "kaise ho aap log", "kya haal hai", "kya hal hai",
    "good morning", "good evening", "good afternoon",
}


def build_twiml_response(reply_text: str) -> Response:
    """Constructs standard TwiML XML response for Twilio WhatsApp."""
    safe_text = (
        reply_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_text}</Message>
</Response>"""
    return Response(content=xml_content, media_type="application/xml", status_code=status.HTTP_200_OK)


async def fetch_twilio_media(media_url: str) -> Optional[bytes]:
    """Downloads media binary from Twilio using HTTP Basic Auth."""
    try:
        auth = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(media_url, auth=auth)
            if resp.status_code == 200:
                return resp.content
            logger.warning(f"Failed to fetch Twilio media: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Error downloading Twilio media from {media_url}: {e}")
    return None


class WebhookOrchestrationService:
    """
    Authoritative Supabase-backed orchestration pipeline for WhatsApp/Twilio webhooks (Phase 3H).
    - Twilio signature authentication (X-Twilio-Signature).
    - Destination-based seller resolution via seller_whatsapp_channels.
    - Distributed MessageSid idempotency via webhook_messages.
    - Authoritative customer lifecycle via CustomerService.
    - Multi-tenant privacy state persisted in Supabase privacy_settings.
    - Media upload to private bucket 'munim-media' via StorageService.
    - Server-authoritative transactional order creation via OrderService RPC.
    - Payment recording with status 'pending' (never auto-verified).
    """

    def __init__(self, db: Optional[Client] = None):
        self.db = db or get_supabase_client()
        self.webhook_repo = WebhookRepository(self.db)
        self.privacy_repo = PrivacyRepository(self.db)
        self.customer_service = CustomerService(self.db)
        self.product_service = ProductService(self.db)
        self.order_service = OrderService(self.db)
        self.payment_service = PaymentService(self.db)
        self.storage_service = StorageService(self.db)
        self.orchestrator = Orchestrator()

    async def process_incoming_webhook(
        self,
        request_url: str,
        form_data: Mapping[str, Any],
        signature: Optional[str],
    ) -> Response:
        """Processes an incoming WhatsApp webhook through the authoritative Supabase pipeline."""

        # 1. Twilio HMAC-SHA1 Signature Verification
        if not validate_twilio_signature(url=request_url, params=form_data, signature=signature):
            logger.warning("Twilio signature validation failed for URL: %s", request_url)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Twilio signature",
            )

        # 2. Extract & Normalize Identifiers
        message_sid = str(form_data.get("MessageSid", "")).strip()
        from_raw = str(form_data.get("From", "")).strip()
        to_raw = str(form_data.get("To", "")).strip()
        from_phone = normalize_whatsapp_phone(from_raw)
        to_phone = normalize_whatsapp_phone(to_raw)
        raw_text = str(form_data.get("Body", "")).strip()
        profile_name = str(form_data.get("ProfileName", "")).strip()

        num_media = int(form_data.get("NumMedia", 0) or 0)
        media_url = str(form_data.get("MediaUrl0", "")).strip()
        media_content_type = str(form_data.get("MediaContentType0", "")).strip()

        if not message_sid or not from_phone:
            logger.warning("Received webhook without valid MessageSid or From phone.")
            return Response(content="OK", status_code=status.HTTP_200_OK)

        # Determine media type
        if num_media > 0:
            if "audio" in media_content_type:
                msg_type = "audio"
            elif "image" in media_content_type:
                msg_type = "image"
            else:
                msg_type = "media"
        else:
            msg_type = "text"

        # 3. Resolve Seller from Incoming Channel ('To')
        seller_id = self.webhook_repo.resolve_seller_by_phone(to_phone)
        if not seller_id:
            logger.warning("Unmapped WhatsApp receiving channel: %s. Quarantining event.", to_phone)
            self.webhook_repo.mark_message_quarantined(
                message_sid=message_sid,
                from_phone=from_phone,
                to_phone=to_phone,
                reason=f"Channel {to_phone} not mapped to any registered active seller",
                raw_text=raw_text,
            )
            return build_twiml_response("This store number is not registered. Please contact the business directly.")

        # 4. Atomic Idempotency Reservation
        is_new, existing_rec = self.webhook_repo.reserve_webhook_message(
            message_sid=message_sid,
            seller_id=seller_id,
            from_phone=from_phone,
            to_phone=to_phone,
            media_type=msg_type,
            raw_text=raw_text,
        )

        if not is_new:
            # Handle duplicate or already processing message
            status_val = (existing_rec or {}).get("processing_status", "duplicate")
            logger.info("Duplicate MessageSid %s (status=%s). Returning cached state.", message_sid, status_val)
            if status_val == WebhookProcessingStatus.COMPLETED.value:
                cached_reply = (existing_rec or {}).get("response_summary") or "Message already processed."
                return build_twiml_response(cached_reply)
            return Response(content="Duplicate message ignored", status_code=status.HTTP_200_OK)

        # Wrap subsequent processing in try/except to mark failure on unhandled exceptions
        try:
            return await self._execute_pipeline(
                seller_id=seller_id,
                message_sid=message_sid,
                from_phone=from_phone,
                to_phone=to_phone,
                raw_text=raw_text,
                profile_name=profile_name,
                msg_type=msg_type,
                num_media=num_media,
                media_url=media_url,
                media_content_type=media_content_type,
            )
        except Exception as e:
            logger.error("Error executing Supabase webhook pipeline for %s: %s", message_sid, e, exc_info=True)
            self.webhook_repo.mark_message_failed(message_sid=message_sid, error_message=str(e))
            return build_twiml_response("Sorry, an error occurred while processing your request. Please try again.")

    async def _execute_pipeline(
        self,
        seller_id: str,
        message_sid: str,
        from_phone: str,
        to_phone: str,
        raw_text: str,
        profile_name: str,
        msg_type: str,
        num_media: int,
        media_url: str,
        media_content_type: str,
    ) -> Response:
        """Executes customer resolution, privacy checks, media ingestion, AI extraction, and order/payment RPCs."""

        # 5. Resolve or Register Customer
        customer = self.customer_service.customer_repo.get_customer_by_phone(
            seller_id=seller_id,
            phone=from_phone,
        )
        if not customer:
            clean_display_name = profile_name or "WhatsApp Customer"
            customer = self.customer_service.create_customer(
                seller_id=seller_id,
                data=CustomerCreateRequest(
                    phone=from_phone,
                    name=clean_display_name,
                    notes=f"Auto-created from WhatsApp webhook channel {to_phone}",
                ),
            )
        customer_id = str(customer.id)
        customer_display_name = customer.name or profile_name or "Customer"

        # 6. Privacy Switches & Mode Evaluation (#private / #resume)
        first_token = raw_text.strip().split()[0].lower() if raw_text.strip() else ""

        if first_token == "#private":
            self.privacy_repo.set_privacy_status(seller_id=seller_id, customer_id=customer_id, is_private=True)
            set_customer_privacy(from_phone, True)  # Local SQLite fallback sync
            reply = "🔒 Munim AI assistant paused for this chat. Type #resume to restart."
            self.webhook_repo.mark_message_completed(message_sid=message_sid, intent="privacy_pause", response_summary=reply)
            return build_twiml_response(reply)

        if first_token == "#resume":
            self.privacy_repo.set_privacy_status(seller_id=seller_id, customer_id=customer_id, is_private=False)
            set_customer_privacy(from_phone, False)  # Local SQLite fallback sync
            reply = "🔓 Munim AI assistant resumed for this chat."
            self.webhook_repo.mark_message_completed(message_sid=message_sid, intent="privacy_resume", response_summary=reply)
            return build_twiml_response(reply)

        # Check existing privacy state
        is_private = self.privacy_repo.get_privacy_status(seller_id=seller_id, customer_id=customer_id)
        if not is_private and is_customer_private_in_db(from_phone):
            is_private = True

        if is_private:
            logger.info("Privacy active for customer %s (%s). Bypassing AI & memory.", customer_id, from_phone)
            self.webhook_repo.mark_message_completed(
                message_sid=message_sid,
                intent="privacy_masked",
                response_summary="[Privacy mode active - AI suppressed]",
            )
            return Response(content="OK", status_code=status.HTTP_200_OK)

        # 7. Instant Fast-Path for Conversational Greetings (< 10ms turnaround)
        clean_text = raw_text.lower().strip()
        clean_no_punct = "".join(c for c in clean_text if c.isalnum() or c.isspace()).strip()
        if msg_type == "text" and (clean_text in FAST_GREETINGS or clean_no_punct in FAST_GREETINGS or not clean_text):
            fast_reply = (
                f"Namaste {customer_display_name}! 🙏 Munim AI par aapka swagat hai.\n\n"
                f"Main aapka personal business assistant hoon. Aap mujhse:\n"
                f"• Available designs aur prices pooch sakte hain\n"
                f"• Naya order book kar sakte hain\n"
                f"• UPI payment screenshot bhej sakte hain\n\n"
                f"Bataiye, aaj aapko kya dekhna hai?"
            )
            self.webhook_repo.mark_message_completed(
                message_sid=message_sid,
                intent="greeting",
                response_summary=fast_reply,
            )
            return build_twiml_response(fast_reply)

        # 8. Check for Owner Commands (summary, pending dues)
        clean_owner = normalize_whatsapp_phone(settings.OWNER_WHATSAPP_NUMBER)
        if clean_owner and from_phone == clean_owner and clean_text in ["summary", "pending dues", "dues", "hisaab"]:
            try:
                summary_data = get_dashboard_summary(seller_id=seller_id, db=self.db)
                summary_reply = (
                    f"📊 *Munim AI — Store Hisaab Summary*\n"
                    f"────────────────────────\n"
                    f"• Monthly Revenue: {summary_data.revenue.formatted}\n"
                    f"• Outstanding Dues: {summary_data.pending_dues.formatted}\n"
                    f"• Active Orders: {summary_data.orders.formatted}\n"
                    f"────────────────────────\n"
                    f"Generated live from Supabase ledger."
                )
            except Exception as sum_err:
                logger.warning("Could not compute live dashboard summary, falling back to legacy: %s", sum_err)
                summary_reply = get_store_summary()

            self.webhook_repo.mark_message_completed(
                message_sid=message_sid,
                intent="owner_summary",
                response_summary=summary_reply,
            )
            return build_twiml_response(summary_reply)

        # 9. Media Ingestion via StorageService (Phase 3G)
        media_bytes = None
        if num_media > 0 and media_url:
            media_bytes = await fetch_twilio_media(media_url)
            if media_bytes:
                try:
                    category = "voice_note" if msg_type == "audio" else "attachment"
                    self.storage_service.upload_media(
                        seller_id=seller_id,
                        file_bytes=media_bytes,
                        original_filename=f"whatsapp_{message_sid[:8]}",
                        declared_content_type=media_content_type or ("audio/ogg" if msg_type == "audio" else "image/jpeg"),
                        category=category,
                        customer_id=customer_id,
                    )
                    logger.info("Successfully uploaded WhatsApp media to Supabase bucket '%s'", self.storage_service.bucket)
                except Exception as store_err:
                    logger.warning("Storage upload failed for media in message %s: %s", message_sid, store_err)

        # 10. Dynamic Catalog Context
        active_products = self.product_service.list_products(seller_id=seller_id, is_active=True, limit=20)
        catalog_summary = ", ".join([f"{p.name} ({p.category or 'General'})" for p in active_products]) if active_products else ""

        # 11. Multimodal AI Extraction
        extracted = None
        timestamp_iso = customer.created_at.isoformat() if hasattr(customer.created_at, "isoformat") else str(customer.created_at)

        if msg_type == "image" and media_bytes:
            extracted = await extract_image(
                image_bytes=media_bytes,
                mime_type=media_content_type or "image/jpeg",
                customer_phone=from_phone,
                message_id=message_sid,
                timestamp=timestamp_iso,
            )
        elif msg_type == "audio" and media_bytes:
            extracted = await extract_audio(
                audio_bytes=media_bytes,
                mime_type=media_content_type or "audio/ogg",
                customer_phone=from_phone,
                message_id=message_sid,
                timestamp=timestamp_iso,
            )

        if not extracted:
            extracted = await extract_text(
                raw_text=raw_text or "[Empty message]",
                customer_phone=from_phone,
                message_id=message_sid,
                timestamp=timestamp_iso,
            )

        intent = str(extracted.type)
        logger.info(f"Extracted intent for {from_phone}: {intent} (confidence: {extracted.confidence.overall})")

        # 12. Authoritative Business Execution (Phase 3D RPC & PaymentService)
        reply = ""

        # A. ORDER INTENT
        if intent == "order" and extracted.items:
            # Match items to active product variants
            order_line_items: List[OrderItemCreateRequest] = []
            for item in extracted.items:
                item_name = (item.name or "").lower().strip()
                matched_variant_id = None

                # Search through seller products
                for prod in active_products:
                    if item_name in prod.name.lower() or prod.name.lower() in item_name:
                        variants = self.product_service.product_repo.list_variants_by_product(
                            seller_id=seller_id,
                            product_id=prod.id,
                        )
                        for var in variants:
                            # Match size if specified
                            if item.size and var.size and str(item.size).lower() == str(var.size).lower():
                                matched_variant_id = var.id
                                break
                            elif not item.size:
                                matched_variant_id = var.id
                                break
                    if matched_variant_id:
                        break

                if matched_variant_id:
                    order_line_items.append(
                        OrderItemCreateRequest(
                            variant_id=matched_variant_id,
                            quantity=max(1, int(item.qty or 1)),
                        )
                    )

            if order_line_items:
                try:
                    order_req = OrderCreateRequest(
                        customer_id=UUID(customer_id),
                        items=order_line_items,
                        currency="INR",
                        notes=f"Created via WhatsApp message {message_sid}",
                    )
                    created_order = self.order_service.create_order_with_reservation(
                        seller_id=seller_id,
                        data=order_req,
                    )
                    reply = (
                        f"✅ *Order Confirmed!* (ID: #{str(created_order.id)[:8].upper()})\n"
                        f"• Total Amount: ₹{created_order.total_amount:,.2f}\n"
                        f"• Status: {created_order.status.capitalize()}\n\n"
                        f"Aapka order book ho gaya hai aur stock reserve ho chuka hai. "
                        f"Payment ke baad screenshot yahan bhej dein."
                    )
                except Exception as order_err:
                    logger.warning("Order creation failed via RPC: %s", order_err)
                    reply = (
                        f"Namaste {customer_display_name}! Stock check mein dikkat aayi: {order_err}. "
                        f"Kripya thodi der baad dobara koshish karein ya store se contact karein."
                    )

        # B. PAYMENT INTENT
        elif intent in ["payment", "partial_payment"] and extracted.amount:
            try:
                pay_amount = Decimal(str(extracted.amount))
                ref = extracted.upi_txn_id or f"WA-{message_sid[:8]}"

                # Attempt to match with existing orders
                matching_order = self.payment_service.find_matching_order(
                    seller_id=seller_id,
                    customer_id=customer_id,
                    amount=pay_amount,
                    transaction_reference=ref,
                )

                linked_order_id = matching_order.id if matching_order else None

                payment_req = PaymentCreateRequest(
                    order_id=linked_order_id,
                    amount=pay_amount,
                    method=PaymentMethod.UPI,
                    status=PaymentStatus.PENDING,  # Strictly pending; never auto-verified
                    transaction_reference=ref,
                )

                recorded_payment = self.payment_service.record_payment(
                    seller_id=seller_id,
                    data=payment_req,
                )

                if linked_order_id:
                    reply = (
                        f"💳 *Payment Received* (₹{pay_amount:,.2f})\n"
                        f"• Linked to Order: #{str(linked_order_id)[:8].upper()}\n"
                        f"• Reference: {ref}\n"
                        f"• Status: Pending Verification ⏳\n\n"
                        f"Aapki payment darj kar li gayi hai. Seller ke verify karne par confirmation bhej diya jayega."
                    )
                else:
                    reply = (
                        f"💳 *Advance / Unlinked Payment Received* (₹{pay_amount:,.2f})\n"
                        f"• Reference: {ref}\n"
                        f"• Status: Pending Verification ⏳\n\n"
                        f"Aapka payment note ho gaya hai. Seller jald hi isse verify karenge."
                    )
            except Exception as pay_err:
                logger.warning("Payment recording failed: %s", pay_err)
                reply = f"Payment note karne mein asuvidha hui: {pay_err}. Kripya screenshot dubara bhejein."

        # C. DEFAULT FALLBACK / CATALOG INQUIRY
        if not reply:
            context = {
                "seller_id": seller_id,
                "customer_id": customer_id,
                "customer_name": customer_display_name,
                "catalog_summary": catalog_summary,
            }
            exec_result = await self.orchestrator.route_and_execute(extracted, context)
            reply = exec_result.get("reply") or (
                f"Namaste {customer_display_name}! 🙏 Aapka sandesh prapt hua.\n"
                f"Humare paas {catalog_summary or 'kurtis aur dresses'} uplabdh hain. "
                f"Bataiye, aapko kya pasand aaya?"
            )

        # 13. Mark Message as Completed
        self.webhook_repo.mark_message_completed(
            message_sid=message_sid,
            intent=intent,
            response_summary=reply,
        )

        return build_twiml_response(reply)
