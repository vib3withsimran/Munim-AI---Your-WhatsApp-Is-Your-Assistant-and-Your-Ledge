import logging
import httpx
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Query, Response, BackgroundTasks, status

from backend.app.core.config import settings
from backend.app.services.db import is_duplicate_message, record_processed_message
from backend.app.ai import extract_text, extract_audio, extract_image
from backend.app.agents import Orchestrator
from backend.app.services.database_service import get_active_seller_id
from backend.app.services.sheets import (
    add_or_update_customer,
    add_order,
    add_payment,
    get_store_summary
)
from backend.app.utils.privacy import check_privacy

logger = logging.getLogger(__name__)
router = APIRouter()
orchestrator = Orchestrator()

GREETING_TOKENS = {
    "hi", "hii", "hiii", "hiiii", "hello", "hellow", "hey", "heyy",
    "namaste", "namasteji", "namaskar", "pranam",
    "kaise", "kya", "haal", "chal", "theek", "ho",
    "good", "morning", "afternoon", "evening",
    "bhaiya", "bhai", "sir", "mam", "ji", "aap", "dost"
}

TRANSACTIONAL_KEYWORDS = {
    "order", "pack", "chahiye", "bhejo", "bhej", "book", "lena",
    "kurti", "saree", "suit", "dress", "size", "color", "colour", "item",
    "product", "catalog", "catalogue", "design", "designs", "photo", "pic", "pics",
    "rate", "price", "kitna", "kitne", "paisa", "rupee", "rs", "cost",
    "payment", "upi", "pay", "paid", "screenshot", "advance", "dues", "hisaab",
    "gpay", "phonepe", "paytm", "parcel", "delivery", "track", "dispatch",
    "same", "purani", "pichli", "again", "repeat", "available", "stock",
    "complaint", "return", "exchange", "refund", "damage", "kharab", "galat",
    "summary"
}

def is_conversational_greeting(raw_text: str) -> bool:
    """Intelligently detects pure greetings with zero business intent in <1ms."""
    clean = raw_text.lower().strip()
    if not clean:
        return True

    clean_no_punct = "".join(c for c in clean if c.isalnum() or c.isspace()).strip()
    words = clean_no_punct.split()
    if not words:
        return True

    # If any transactional or business keyword exists, route to AI / Agents
    if any(kw in clean_no_punct for kw in TRANSACTIONAL_KEYWORDS):
        return False

    # If short conversational message containing greeting tokens, it's a greeting
    greeting_count = sum(1 for w in words if w in GREETING_TOKENS)
    if len(words) <= 6 and greeting_count >= 1:
        return True

    return False

def build_twiml_response(reply_text: str) -> Response:
    """Builds standard TwiML XML response for Twilio WhatsApp (bypasses ContentSid restriction)."""
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


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """GET /webhook healthcheck and handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verification handshake successful!")
        return Response(content=hub_challenge, media_type="text/plain", status_code=status.HTTP_200_OK)

    return {
        "status": "online",
        "service": "Munim AI Twilio & WhatsApp Webhook",
        "time": datetime.now().isoformat()
    }


def background_sync_sheets(extracted, sender_phone: str, customer_display_name: str):
    """Executes Google Sheets synchronization in the background as a safe backup."""
    try:
        add_or_update_customer(
            phone=sender_phone,
            name=customer_display_name,
            status="active"
        )
        if extracted.type == "order":
            add_order(extracted)
        elif extracted.type in ["payment", "partial_payment"]:
            add_payment(extracted)
    except Exception as e:
        logger.error(f"Error in background Google Sheets sync: {e}")


async def fetch_twilio_media(media_url: str) -> Optional[bytes]:
    """
    Downloads media file (image/audio) from Twilio Media URL using Twilio Basic Auth.
    """
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


@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handles incoming WhatsApp messages from Twilio with sub-1s fast path,
    multimodal processing (images & audio), and Phase 3 multi-agent routing.
    """
    content_type = request.headers.get("content-type", "")

    message_id = ""
    sender_phone = ""
    contact_name = ""
    raw_text = ""
    msg_type = "text"
    media_url = ""
    media_content_type = ""
    timestamp_iso = datetime.now().isoformat()

    # 1. Parse incoming Twilio Form or JSON mock
    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        message_id = form_data.get("MessageSid", "")
        from_raw = form_data.get("From", "")
        sender_phone = from_raw.replace("whatsapp:", "").replace("+", "").strip()
        contact_name = form_data.get("ProfileName", "")
        raw_text = form_data.get("Body", "").strip()

        num_media = int(form_data.get("NumMedia", 0) or 0)
        if num_media > 0:
            media_content_type = form_data.get("MediaContentType0", "")
            media_url = form_data.get("MediaUrl0", "")
            if "audio" in media_content_type:
                msg_type = "audio"
            elif "image" in media_content_type:
                msg_type = "image"
            else:
                msg_type = "media"
    else:
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
        return Response(content="OK", status_code=status.HTTP_200_OK)

    # 2. Deduplication Check (SQLite)
    if is_duplicate_message(message_id):
        logger.info(f"Duplicate message ignored: {message_id}")
        return Response(content="Duplicate ignored", status_code=status.HTTP_200_OK)

    record_processed_message(
        message_id=message_id,
        sender_phone=sender_phone,
        media_type=msg_type,
        raw_text=raw_text
    )

    logger.info(f"Processing Twilio message from {sender_phone} ({contact_name}): '{raw_text}' [type={msg_type}]")

    # 3. Privacy Filter Check (#private / #resume)
    is_private, _ = check_privacy(sender_phone, raw_text)
    if is_private:
        logger.info(f"Privacy active for {sender_phone}. Bypassing AI & storage.")
        if raw_text.strip().lower().startswith("#private"):
            return build_twiml_response("🔒 Munim AI assistant paused for this chat. Type #resume to restart.")
        return Response(content="OK", status_code=status.HTTP_200_OK)

    if raw_text.strip().lower().startswith("#resume"):
        return build_twiml_response("🔓 Munim AI assistant resumed for this chat.")

    # 4. Instant Fast-Path for Conversational Greetings (< 10ms turnaround)
    if msg_type == "text" and is_conversational_greeting(raw_text):
        name_disp = contact_name or "Ji"
        fast_reply = (
            f"Namaste {name_disp}! 🙏 Munim AI par aapka swagat hai.\n\n"
            f"Main aapka personal business assistant hoon. Aap mujhse:\n"
            f"• Available designs aur prices pooch sakte hain\n"
            f"• Naya order book kar sakte hain\n"
            f"• UPI payment screenshot bhej sakte hain\n\n"
            f"Bataiye, aaj aapko kya dekhna hai?"
        )
        logger.info(f"Instant greeting fast-path triggered for {sender_phone} (<5ms)")
        return build_twiml_response(fast_reply)

    # 5. Check for Owner Commands (summary, pending dues)
    clean_sender = sender_phone.replace("+", "").strip()
    clean_owner = settings.OWNER_WHATSAPP_NUMBER.replace("+", "").strip()
    if clean_sender and clean_sender == clean_owner and clean_text in ["summary", "pending dues", "dues", "hisaab"]:
        summary_text = get_store_summary()
        return build_twiml_response(summary_text)

    # 6. Multimodal Extraction Pipeline (Groq for Text, Gemini for Audio & Images)
    extracted = None

    if msg_type == "image" and media_url:
        logger.info(f"Downloading image from Twilio: {media_url}")
        img_bytes = await fetch_twilio_media(media_url)
        if img_bytes:
            extracted = await extract_image(
                image_bytes=img_bytes,
                mime_type=media_content_type or "image/jpeg",
                customer_phone=sender_phone,
                message_id=message_id,
                timestamp=timestamp_iso
            )

    elif msg_type == "audio" and media_url:
        logger.info(f"Downloading audio voice note from Twilio: {media_url}")
        aud_bytes = await fetch_twilio_media(media_url)
        if aud_bytes:
            extracted = await extract_audio(
                audio_bytes=aud_bytes,
                mime_type=media_content_type or "audio/ogg",
                customer_phone=sender_phone,
                message_id=message_id,
                timestamp=timestamp_iso
            )

    # Default to text extraction
    if not extracted:
        extracted = await extract_text(
            raw_text=raw_text or "[Empty message]",
            customer_phone=sender_phone,
            message_id=message_id,
            timestamp=timestamp_iso
        )

    logger.info(f"Extracted intent for {sender_phone}: {extracted.type} (confidence: {extracted.confidence.overall})")

    # 7. Route through Phase 3 Orchestrator & Agents
    seller_uuid = get_active_seller_id()
    context = {
        "seller_id": seller_uuid,
        "customer_id": sender_phone,
        "customer_name": contact_name or extracted.customer_name or "Ji"
    }
    execution_result = await orchestrator.route_and_execute(extracted, context)

    # 8. Background Safety Sync to Google Sheets
    customer_display_name = extracted.customer_name or contact_name
    background_tasks.add_task(
        background_sync_sheets,
        extracted=extracted,
        sender_phone=sender_phone,
        customer_display_name=customer_display_name
    )

    # 9. Return Instant TwiML XML Response to Customer
    reply_text = execution_result.get("reply", "")
    if reply_text:
        logger.info(f"Delivering reply via {execution_result.get('agent_used')}: {reply_text[:60]}...")
        return build_twiml_response(reply_text)

    return Response(content="OK", status_code=status.HTTP_200_OK)
