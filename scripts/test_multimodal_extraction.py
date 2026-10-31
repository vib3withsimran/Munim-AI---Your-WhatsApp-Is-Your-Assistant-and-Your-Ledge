import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import json
from backend.app.ai import (
    extract_text,
    normalize_message,
    generate_smart_reply,
    generate_owner_alert
)
from backend.app.models.schemas import ExtractedMessage

def test_multimodal_normalization():
    print("=== Testing Multimodal Schema Normalization ===")
    
    # 1. Text payload
    text_raw = {
        "type": "order",
        "customer_name": "Priya Sharma",
        "items": [
            {"name": "Anarkali Kurti", "qty": 2, "size": "M", "color": "Blue", "unit_price": 1299}
        ],
        "amount": 2598.0,
        "delivery_address": "Sector 14, Gurgaon",
        "confidence": {"overall": 0.95, "items": 0.95, "amount": 0.95},
        "reply_needed": True
    }
    msg_text = normalize_message(
        raw_data=text_raw,
        media_type="text",
        customer_phone="919876543210",
        raw_text="2 anarkali kurti bhejo M size mein"
    )
    assert isinstance(msg_text, ExtractedMessage)
    assert msg_text.media_type == "text"
    assert msg_text.type == "order"
    assert len(msg_text.items) == 1
    assert msg_text.items[0].qty == 2
    assert msg_text.amount == 2598.0
    print("[PASS] Text normalization verified")

    # 2. Audio payload (simulating voice note extraction)
    audio_raw = {
        "transcription": "Didi teen black kurti XL size me bhej do, jaldi chahiye",
        "type": "order",
        "items": [
            {"name": "Black Kurti", "qty": 3, "size": "XL", "color": "Black", "unit_price": 899}
        ],
        "amount": 2697.0,
        "confidence": {"overall": 0.91, "items": 0.92, "amount": 0.90},
        "reply_needed": True
    }
    msg_audio = normalize_message(
        raw_data=audio_raw,
        media_type="audio",
        customer_phone="919876543211",
        raw_text=audio_raw["transcription"]
    )
    assert isinstance(msg_audio, ExtractedMessage)
    assert msg_audio.media_type == "audio"
    assert msg_audio.type == "order"
    assert msg_audio.items[0].qty == 3
    assert msg_audio.raw_text.startswith("Didi teen black")
    print("[PASS] Audio normalization verified")

    # 3. Image payload (simulating UPI screenshot extraction)
    image_raw = {
        "summary": "Google Pay screenshot showing ₹2,598 paid successfully to Neha Closet",
        "type": "payment",
        "amount": 2598.0,
        "upi_txn_id": "409281726351",
        "confidence": {"overall": 0.98, "items": 1.0, "amount": 0.99},
        "reply_needed": True
    }
    msg_image = normalize_message(
        raw_data=image_raw,
        media_type="image",
        customer_phone="919876543210",
        raw_text=image_raw["summary"]
    )
    assert isinstance(msg_image, ExtractedMessage)
    assert msg_image.media_type == "image"
    assert msg_image.type == "payment"
    assert msg_image.amount == 2598.0
    assert msg_image.upi_txn_id == "409281726351"
    print("[PASS] Image UPI normalization verified")

    # 4. Low-confidence escalation test
    low_conf_raw = {
        "summary": "Blurry receipt with partial amount",
        "type": "payment",
        "amount": 500.0,
        "confidence": {"overall": 0.60, "items": 0.5, "amount": 0.6},
        "reply_needed": True
    }
    msg_low_conf = normalize_message(
        raw_data=low_conf_raw,
        media_type="image",
        customer_phone="919876543210"
    )
    assert msg_low_conf.escalate_to_owner is True
    assert "Low extraction confidence" in (msg_low_conf.escalation_reason or "")
    print("[PASS] Low-confidence escalation verified")

    # 5. Smart reply and Owner alert test
    reply_text = generate_smart_reply(msg_text)
    assert "Namaste" in reply_text
    assert "Anarkali Kurti" in reply_text
    
    reply_pay = generate_smart_reply(msg_image)
    assert "409281726351" in reply_pay
    
    owner_alert = generate_owner_alert(msg_low_conf)
    assert "*Munim AI Owner Alert*" in owner_alert
    print("[PASS] Smart reply & owner alert generators verified")

    print("\nALL PHASE 1 MULTIMODAL NORMALIZATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_multimodal_normalization()
