import logging
from datetime import datetime
from typing import Dict, Any, Optional

from backend.app.models.schemas import ExtractedMessage, OrderItem, ConfidenceScore

logger = logging.getLogger(__name__)

VALID_TYPES = {
    "order",
    "payment",
    "partial_payment",
    "question",
    "catalog_query",
    "delivery_query",
    "complaint",
    "command",
    "unknown"
}

def normalize_message(
    raw_data: Dict[str, Any],
    media_type: str,
    customer_phone: str,
    raw_text: str = "",
    message_id: str = "",
    timestamp: Optional[str] = None
) -> ExtractedMessage:
    """
    Normalizes raw structured dicts from text, audio, or image extractors
    into a strictly uniform ExtractedMessage instance.
    """
    if not timestamp:
        timestamp = datetime.now().isoformat()

    # Extract & validate type
    extracted_type = str(raw_data.get("type", "unknown")).lower().strip()
    if extracted_type not in VALID_TYPES:
        extracted_type = "unknown"

    # Extract order items
    items = []
    raw_items = raw_data.get("items", [])
    if isinstance(raw_items, list):
        for it in raw_items:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name", "")).strip()
            if not name:
                continue
            try:
                qty = int(it.get("qty", 1))
            except (ValueError, TypeError):
                qty = 1
            
            unit_price = None
            if it.get("unit_price") is not None:
                try:
                    unit_price = float(it["unit_price"])
                except (ValueError, TypeError):
                    unit_price = None

            items.append(
                OrderItem(
                    name=name,
                    qty=qty,
                    size=str(it.get("size")) if it.get("size") else None,
                    color=str(it.get("color")) if it.get("color") else None,
                    unit_price=unit_price
                )
            )

    # Extract amount
    amount = None
    if raw_data.get("amount") is not None:
        try:
            amount = float(raw_data["amount"])
        except (ValueError, TypeError):
            amount = None

    # Confidence scores
    conf_raw = raw_data.get("confidence", {})
    if isinstance(conf_raw, dict):
        try:
            overall = float(conf_raw.get("overall", 0.9))
        except (ValueError, TypeError):
            overall = 0.9
        try:
            c_items = float(conf_raw.get("items", 0.9))
        except (ValueError, TypeError):
            c_items = 0.9
        try:
            c_amount = float(conf_raw.get("amount", 0.9))
        except (ValueError, TypeError):
            c_amount = 0.9
    else:
        overall, c_items, c_amount = 0.85, 0.85, 0.85

    # Clamp confidence values
    overall = max(0.0, min(1.0, overall))
    c_items = max(0.0, min(1.0, c_items))
    c_amount = max(0.0, min(1.0, c_amount))

    confidence = ConfidenceScore(
        overall=overall,
        items=c_items,
        amount=c_amount
    )

    # Escalation policy
    escalate = bool(raw_data.get("escalate_to_owner", False))
    escalation_reason = raw_data.get("escalation_reason")

    if overall < 0.75:
        escalate = True
        if not escalation_reason:
            escalation_reason = f"Low extraction confidence ({overall:.2f}); owner review recommended."

    if extracted_type in ["complaint", "partial_payment"]:
        escalate = True
        if not escalation_reason:
            escalation_reason = f"Escalated due to category: {extracted_type}."

    # Effective raw text (fallback to transcribed or summary text if not explicitly given)
    effective_text = raw_text or str(raw_data.get("transcription") or raw_data.get("summary") or "")

    return ExtractedMessage(
        message_id=message_id,
        timestamp=timestamp,
        media_type=media_type if media_type in ["text", "audio", "image"] else "text",
        type=extracted_type,
        customer_phone=customer_phone,
        customer_name=str(raw_data.get("customer_name")).strip() if raw_data.get("customer_name") else None,
        items=items,
        amount=amount,
        upi_txn_id=str(raw_data.get("upi_txn_id")).strip() if raw_data.get("upi_txn_id") else None,
        linked_order_id=str(raw_data.get("linked_order_id")).strip() if raw_data.get("linked_order_id") else None,
        delivery_address=str(raw_data.get("delivery_address")).strip() if raw_data.get("delivery_address") else None,
        raw_text=effective_text,
        confidence=confidence,
        reply_needed=bool(raw_data.get("reply_needed", True)),
        escalate_to_owner=escalate,
        escalation_reason=escalation_reason
    )

