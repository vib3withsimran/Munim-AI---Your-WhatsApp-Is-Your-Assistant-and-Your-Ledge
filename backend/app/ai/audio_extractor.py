import logging
from datetime import datetime
from typing import Optional, Dict, Any

from backend.app.models.schemas import ExtractedMessage
from backend.app.ai.gemini import call_gemini
from backend.app.ai.normalize_message import normalize_message

logger = logging.getLogger(__name__)

AUDIO_EXTRACTION_SYSTEM_PROMPT = """
You are 'Munim AI', an expert assistant for Indian home businesses.
You have been given an audio recording (voice note) from a customer via WhatsApp.
Customers often speak in Hindi, Hinglish, or English with regional accents (e.g. "Didi do blue anarkali kurti pack kar dena L size me, aur ek black wala").

Your task:
1. Accurately transcribe what the customer said in the voice note. Store this in the "transcription" field.
2. Analyze the customer's intent and extract structured commercial information.

Output JSON Schema:
{
  "transcription": string,
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

Guidelines:
- If background noise or audio is muffled, lower the confidence score (< 0.70) and set "escalate_to_owner": true.
- Extract quantities accurately (e.g., "do" = 2, "teen" = 3, "ek darjan" = 12, "adha kilo" = 0.5kg/1 item).
- Return ONLY the JSON object.
"""

async def extract_audio(
    audio_bytes: bytes,
    mime_type: str,
    customer_phone: str,
    message_id: str = "",
    timestamp: Optional[str] = None,
    context: Optional[str] = None
) -> ExtractedMessage:
    """
    Extracts transcription and structured message data from WhatsApp audio / voice note using Gemini Multimodal Audio.
    """
    if not timestamp:
        timestamp = datetime.now().isoformat()

    prompt = f"Customer Phone: {customer_phone}\nPlease listen to this WhatsApp audio voice note, transcribe it, and extract structured order/inquiry data."
    if context:
        prompt += f"\nStore Catalog Context:\n{context}"

    parsed = await call_gemini(
        prompt=prompt,
        system_instruction=AUDIO_EXTRACTION_SYSTEM_PROMPT,
        media_bytes=audio_bytes,
        media_mime_type=mime_type,
        temperature=0.1,
        timeout=20.0
    )

    if parsed:
        transcription = parsed.get("transcription", "")
        return normalize_message(
            raw_data=parsed,
            media_type="audio",
            customer_phone=customer_phone,
            raw_text=transcription,
            message_id=message_id,
            timestamp=timestamp
        )

    # Fallback on failure
    return normalize_message(
        raw_data={
            "type": "unknown",
            "confidence": {"overall": 0.4, "items": 0.4, "amount": 0.4},
            "escalate_to_owner": True,
            "escalation_reason": "Audio transcription/extraction failed. Please review audio manually."
        },
        media_type="audio",
        customer_phone=customer_phone,
        raw_text="[Audio note processing error]",
        message_id=message_id,
        timestamp=timestamp
    )

