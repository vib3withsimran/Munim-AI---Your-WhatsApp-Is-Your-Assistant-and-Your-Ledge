import logging
from datetime import datetime
from typing import Optional, Dict, Any

from backend.app.models.schemas import ExtractedMessage
from backend.app.ai.gemini import call_gemini
from backend.app.ai.normalize_message import normalize_message

logger = logging.getLogger(__name__)

IMAGE_EXTRACTION_SYSTEM_PROMPT = """
You are 'Munim AI', an expert visual analysis assistant for Indian home sellers and merchants.
You are given an image received via WhatsApp. The image is typically one of three types:
1. UPI Payment Screenshot (PhonePe, Google Pay, Paytm, BHIM, CRED, Bank app):
   - Locate the exact amount paid (in INR, e.g. ₹1,450).
   - Locate the 12-digit UPI Transaction ID / UTR Reference Number (e.g. 409281726351 or UPI Ref No).
   - Check payment status (Success, Completed, Pending, Failed).
   - Extract Payee name and Payer name if visible.
   - Set "type": "payment" (or "partial_payment" if marked advance).
   - Set confidence.overall high (> 0.95) if UTR and amount are clearly legible.

2. Handwritten Order List / Notebook page:
   - Perform OCR on handwritten or printed list in English / Hindi / Hinglish.
   - Extract item names, quantities, sizes, and any listed prices.
   - Set "type": "order".
   - Include brief transcription in "summary".

3. Product Photo / Catalog Screenshot:
   - Customer inquiring about a product photo or color option.
   - Identify product category, color, features.
   - Set "type": "catalog_query" or "order".

Output JSON Schema:
{
  "summary": string (brief visual description of what is in the image),
  "type": "payment" | "order" | "partial_payment" | "catalog_query" | "question" | "complaint" | "unknown",
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
  "amount": number or null (e.g. 1450.0),
  "upi_txn_id": string or null (e.g. "409281726351"),
  "payment_status": "success" | "pending" | "failed" | null,
  "confidence": {
    "overall": number (0.0 to 1.0),
    "items": number (0.0 to 1.0),
    "amount": number (0.0 to 1.0)
  },
  "reply_needed": boolean,
  "escalate_to_owner": boolean,
  "escalation_reason": string or null
}

Escalation Rules:
- If payment screenshot is blurry or UTR number is partially cut off, set confidence.overall < 0.70 and "escalate_to_owner": true.
- If payment status is "failed" or "pending", escalate to owner immediately.
"""

async def extract_image(
    image_bytes: bytes,
    mime_type: str,
    customer_phone: str,
    message_id: str = "",
    timestamp: Optional[str] = None,
    context: Optional[str] = None
) -> ExtractedMessage:
    """
    Extracts structured payment or order data from WhatsApp images (UPI screenshots, handwritten notes, product photos).
    """
    if not timestamp:
        timestamp = datetime.now().isoformat()

    prompt = f"Customer Phone: {customer_phone}\nAnalyze this image. If it is a UPI receipt, extract UTR reference ID and amount. If it is a handwritten note, extract order items."
    if context:
        prompt += f"\nStore Catalog Context:\n{context}"

    parsed = await call_gemini(
        prompt=prompt,
        system_instruction=IMAGE_EXTRACTION_SYSTEM_PROMPT,
        media_bytes=image_bytes,
        media_mime_type=mime_type,
        temperature=0.1,
        timeout=20.0
    )

    if parsed:
        summary = parsed.get("summary", "")
        return normalize_message(
            raw_data=parsed,
            media_type="image",
            customer_phone=customer_phone,
            raw_text=summary,
            message_id=message_id,
            timestamp=timestamp
        )

    # Fallback on failure
    return normalize_message(
        raw_data={
            "type": "unknown",
            "confidence": {"overall": 0.4, "items": 0.4, "amount": 0.4},
            "escalate_to_owner": True,
            "escalation_reason": "Image visual processing failed. Please verify image manually."
        },
        media_type="image",
        customer_phone=customer_phone,
        raw_text="[Image processing error]",
        message_id=message_id,
        timestamp=timestamp
    )

