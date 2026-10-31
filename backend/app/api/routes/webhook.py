import logging
from datetime import datetime
from fastapi import APIRouter, Request, Query, Response, status

from backend.app.core.config import settings
from backend.app.services.db import is_duplicate_message, record_processed_message
from backend.app.services.whatsapp import send_whatsapp_message
from backend.app.services.ai import analyze_message, generate_smart_reply
from backend.app.services.sheets import (
    add_or_update_customer,
    add_order,
    add_payment,
    get_catalog,
    get_store_summary
)
from backend.app.utils.privacy import check_privacy

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    GET /webhook endpoint:
    - Provides a quick healthcheck in browser
    - Supports Meta handshake if needed
    """
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification handshake successful!")
        return Response(content=hub_challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    
    return {
        "status": "online",
        "service": "Munim AI Twilio & WhatsApp Webhook",
        "time": datetime.now().isoformat()
    }


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handles incoming WhatsApp messages from Twilio (and JSON mocks).
    Twilio sends data as 'application/x-www-form-urlencoded'.
    """
    content_type = request.headers.get("content-type", "")

    # 1. Parse incoming message (Twilio Form or JSON)
    message_id = ""
    sender_phone = ""
    contact_name = ""
    raw_text = ""
    msg_type = "text"
    timestamp_iso = datetime.now().isoformat()

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        message_id = form_data.get("MessageSid", "")
        from_raw = form_data.get("From", "")
        # Clean 'whatsapp:+919876543210' -> '919876543210'
        sender_phone = from_raw.replace("whatsapp:", "").replace("+", "").strip()
        contact_name = form_data.get("ProfileName", "")
        raw_text = form_data.get("Body", "").strip()
        
        num_media = int(form_data.get("NumMedia", 0) or 0)
        if num_media > 0:
            media_content_type = form_data.get("MediaContentType0", "")
            if "audio" in media_content_type:
                msg_type = "audio"
                raw_text = raw_text or "[Voice Note / Audio Message]"
            elif "image" in media_content_type:
                msg_type = "image"
                raw_text = raw_text or "[Image Message / UPI Screenshot]"
            else:
                msg_type = "media"
    else:
        # Fallback for JSON test payloads (mock test suite)
        try:
            data = await request.json()
            entries = data.get("entry", [])
            for entry in entries:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    contacts = value.get("contacts", [])
                    contact_name = contacts[0].get("profile", {}).get("name") if contacts else ""
                    messages = value.get("messages", [])
                    if messages:
                        msg = messages[0]
                        message_id = msg.get("id", "")
                        sender_phone = msg.get("from", "").replace("+", "").strip()
                        msg_type = msg.get("type", "text")
                        raw_text = msg.get("text", {}).get("body", "")
        except Exception as e:
            logger.error(f"Error parsing incoming JSON: {e}")
            return Response(content="Invalid payload", status_code=status.HTTP_400_BAD_REQUEST)

    if not sender_phone or not message_id:
        # Empty heartbeat / ping from provider
        return {"status": "success"}

    # 2. Deduplication Check (SQLite)
    if is_duplicate_message(message_id):
        logger.info(f"Duplicate message ignored: {message_id}")
        return Response(content="Duplicate ignored", status_code=status.HTTP_200_OK)

    # Record message ID in SQLite
    record_processed_message(
        message_id=message_id,
        sender_phone=sender_phone,
        media_type=msg_type,
        raw_text=raw_text
    )

    logger.info(f"Processing Twilio message from {sender_phone} ({contact_name}): '{raw_text}'")

    # 3. Privacy Filter Check (#private / #resume)
    is_private, _ = check_privacy(sender_phone, raw_text)
    if is_private:
        logger.info(f"Privacy active for {sender_phone}. Bypassing AI & storage.")
        if raw_text.strip().lower().startswith("#private"):
            await send_whatsapp_message(sender_phone, "🔒 Munim AI assistant paused for this chat. Type #resume to restart.")
        return {"status": "success"}

    if raw_text.strip().lower().startswith("#resume"):
        await send_whatsapp_message(sender_phone, "🔓 Munim AI assistant resumed for this chat.")
        return {"status": "success"}

    # 4. Check for Owner Commands (summary, pending dues)
    clean_sender = sender_phone.replace("+", "").strip()
    clean_owner = settings.OWNER_WHATSAPP_NUMBER.replace("+", "").strip()
    lower_text = raw_text.strip().lower()

    if clean_sender and clean_sender == clean_owner and lower_text in ["summary", "pending dues", "dues", "hisaab"]:
        summary_text = get_store_summary()
        await send_whatsapp_message(sender_phone, summary_text)
        return {"status": "success"}

    # 5. AI Extraction (Gemini)
    catalog = get_catalog()
    catalog_summary = "\n".join([
        f"- {c.get('name')}: ₹{c.get('price')} (Sizes/Details: {c.get('description', '')})"
        for c in catalog
    ])

    extracted = await analyze_message(
        raw_text=raw_text,
        customer_phone=sender_phone,
        message_id=message_id,
        timestamp=timestamp_iso,
        media_type=msg_type,
        catalog_summary=catalog_summary
    )

    logger.info(f"Extracted intent for {sender_phone}: {extracted.type} (confidence: {extracted.confidence.overall})")

    # 6. Update Google Sheets (Customers, Orders, Payments)
    customer_display_name = extracted.customer_name or contact_name
    add_or_update_customer(
        phone=sender_phone,
        name=customer_display_name,
        status="active"
    )

    if extracted.type == "order":
        add_order(extracted)

    elif extracted.type in ["payment", "partial_payment"]:
        add_payment(extracted)

    # 7. Owner Escalation Check (low confidence / discount / complaint)
    if extracted.escalate_to_owner and clean_owner:
        reason = extracted.escalation_reason or "Customer inquiry requires owner attention."
        escalation_alert = (
            "🚨 *Munim AI Alert — Attention Needed*\n"
            f"• Customer: +{sender_phone} ({customer_display_name or 'Unknown'})\n"
            f"• Type: {extracted.type}\n"
            f"• Reason: {reason}\n"
            f"• Message: \"{raw_text}\""
        )
        await send_whatsapp_message(clean_owner, escalation_alert)
        logger.info(f"Escalated message to owner ({clean_owner}).")

    # 8. Customer Auto-Reply
    if extracted.reply_needed:
        reply_text = generate_smart_reply(extracted, catalog)
        await send_whatsapp_message(sender_phone, reply_text)
        logger.info(f"Replied to customer {sender_phone}: {reply_text[:60]}...")

    return {"status": "success"}
