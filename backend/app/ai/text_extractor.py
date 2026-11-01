import json
import logging
import httpx
from datetime import datetime
from typing import Optional, Dict, Any

from backend.app.core.config import settings
from backend.app.models.schemas import ExtractedMessage, ConfidenceScore
from backend.app.ai.gemini import call_gemini
from backend.app.ai.normalize_message import normalize_message

logger = logging.getLogger(__name__)

TEXT_EXTRACTION_SYSTEM_PROMPT = """
You are 'Munim AI', an expert business assistant and ledger manager for Indian small businesses and home sellers.
Analyze the customer's text message (in English, Hindi, or Hinglish) and return a strictly structured JSON object.

Output JSON Schema:
{
  "type": "order" | "payment" | "partial_payment" | "question" | "catalog_query" | "delivery_query" | "complaint" | "command" | "unknown",
  "customer_name": string or null,
  "items": [
    {
      "name": string,
      "qty": integer,
      "size": string or null,
      "color": string or null,
      "unit_price": number or null
    }
  ],
  "amount": number or null,
  "upi_txn_id": string or null,
  "linked_order_id": string or null,
  "delivery_address": string or null,
  "confidence": {
    "overall": number (0.0 to 1.0),
    "items": number (0.0 to 1.0),
    "amount": number (0.0 to 1.0)
  },
  "reply_needed": boolean,
  "escalate_to_owner": boolean,
  "escalation_reason": string or null
}

Classification Guide:
- "order": intent to purchase (e.g. "bhaiya 2 anarkali kurti pack kardo L size mein", "send 3 samosa", "1 red dress")
- "payment": statement of payment or transaction ref (e.g. "maine ₹850 bhej diye hain", "paid via gpay ref 409827182910")
- "partial_payment": advance/token amount (e.g. "500 abhi diya hai, baaki delivery pe doongi")
- "catalog_query": asking prices, sizes, availability (e.g. "kurti ka rate kya hai?", "catalog send karo")
- "delivery_query": order status / dispatch time (e.g. "mera order kab tak aayega?")
- "complaint": damage, wrong item, refund (e.g. "size galat bhej diya", "fabric torn")
- "command": owner instructions (e.g. "summary", "pending dues", "#private", "#resume")
- "question": generic inquiry
- "unknown": casual chatter, emojis
"""

async def extract_text(
    raw_text: str,
    customer_phone: str,
    message_id: str = "",
    timestamp: Optional[str] = None,
    context: Optional[str] = None
) -> ExtractedMessage:
    """
    Extracts structured intent and items from a text message.
    Uses Groq for fast execution (<1s) and falls back to Gemini.
    """
    if not timestamp:
        timestamp = datetime.now().isoformat()

    clean_text = raw_text.strip()
    if not clean_text or clean_text.lower() in ["hi", "hello", "hey", "namaste", "pranam"]:
        return ExtractedMessage(
            message_id=message_id,
            timestamp=timestamp,
            media_type="text",
            type="question" if clean_text else "unknown",
            customer_phone=customer_phone,
            raw_text=raw_text,
            confidence=ConfidenceScore(overall=1.0, items=1.0, amount=1.0),
            reply_needed=True,
            escalate_to_owner=False
        )

    user_prompt = f"Customer Phone: {customer_phone}\nMessage: \"{clean_text}\""
    if context:
        user_prompt += f"\nAdditional Store/Catalog Context:\n{context}"

    # 1. Fast-Path: Groq API
    if settings.GROQ_API_KEY:
        try:
            groq_url = "https://api.groq.com/openai/v1/chat/completions"
            groq_payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": TEXT_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.post(
                    groq_url,
                    json=groq_payload,
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    parsed = json.loads(data["choices"][0]["message"]["content"].strip())
                    logger.info("Text extraction succeeded via Groq fast-path.")
                    return normalize_message(parsed, "text", customer_phone, raw_text, message_id, timestamp)
        except Exception as e:
            logger.warning(f"Groq text extraction fallback to Gemini: {e}")

    # 2. Multimodal Fallback: Gemini API
    parsed = await call_gemini(
        prompt=user_prompt,
        system_instruction=TEXT_EXTRACTION_SYSTEM_PROMPT,
        temperature=0.1
    )
    if parsed:
        return normalize_message(parsed, "text", customer_phone, raw_text, message_id, timestamp)

    # 3. Fallback on complete failure
    return normalize_message(
        {
            "type": "unknown",
            "confidence": {"overall": 0.5, "items": 0.5, "amount": 0.5},
            "escalate_to_owner": True,
            "escalation_reason": "Text extraction failed on both Groq and Gemini."
        },
        media_type="text",
        customer_phone=customer_phone,
        raw_text=raw_text,
        message_id=message_id,
        timestamp=timestamp
    )

