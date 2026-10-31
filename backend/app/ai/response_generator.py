import logging
from typing import List, Dict, Any, Optional

from backend.app.models.schemas import ExtractedMessage

logger = logging.getLogger(__name__)

def generate_smart_reply(extracted: ExtractedMessage, catalog: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Generates a natural, professional yet warm Hinglish auto-reply tailored for Indian small sellers.
    """
    msg_type = extracted.type
    name = extracted.customer_name or "Ji"

    if msg_type == "order":
        items_str = extracted.items_readable() or "aapka order"
        amt_str = f" Total amount: ₹{int(extracted.amount)}." if extracted.amount else ""
        return (
            f"Namaste {name}! 🙏\n\n"
            f"Aapka order note kar liya gaya hai:\n📦 {items_str}.{amt_str}\n\n"
            f"Kripya apna delivery address bhej dijiye aur payment UPI se confirm karein."
        )

    elif msg_type == "payment":
        amt_str = f"₹{int(extracted.amount)} " if extracted.amount else ""
        utr_str = f"\nUPI Ref / UTR: {extracted.upi_txn_id}" if extracted.upi_txn_id else ""
        return (
            f"Dhanyawaad {name}! 🙏\n\n"
            f"Aapki {amt_str}payment successfully record kar li gayi hai.{utr_str}\n"
            f"Aapka parcel pack karke jald se jald dispatch kar diya jayega!"
        )

    elif msg_type == "partial_payment":
        amt_str = f"₹{int(extracted.amount)} " if extracted.amount else ""
        return (
            f"Namaste {name}! 🙏\n\n"
            f"Aapka advance {amt_str}mil gaya hai. Remaining amount delivery ke time clear kar sakte hain.\n"
            f"Aapka order process ho raha hai!"
        )

    elif msg_type == "catalog_query":
        return (
            f"Namaste {name}! 🙏\n\n"
            f"Hamare latest designs aur prices dekhne ke liye catalog link:\n"
            f"👉 https://munimai.in/catalog\n\n"
            f"Koi specific size (S, M, L, XL, XXL) ya color chahiye toh zaroor batayein!"
        )

    elif msg_type == "delivery_query":
        return (
            f"Namaste {name}! 🙏\n\n"
            f"Aapka parcel dispatch process mein hai. Tracking details aur delivery updates aapko yahan message kar diye jayenge."
        )

    elif msg_type == "complaint":
        return (
            f"Namaste {name}! 🙏\n\n"
            f"Humein khed hai ki aapko pareshani hui. Hamari team aapse jald hi personally connect karegi is issue ko resolve karne ke liye."
        )

    # General inquiry fallback
    return (
        f"Namaste {name}! 🙏 Munim AI par aapka swagat hai.\n"
        f"Aap order place kar sakte hain, UPI payment screenshot bhej sakte hain, ya catalog ke baare mein pooch sakte hain. Hum aapki madad ke liye taiyar hain!"
    )


def generate_owner_alert(extracted: ExtractedMessage) -> str:
    """
    Generates a high-priority WhatsApp or push notification message for the business owner.
    Used when confidence is low or owner confirmation/review is required.
    """
    reason = extracted.escalation_reason or "Review required"
    amt_str = f"₹{int(extracted.amount)}" if extracted.amount else "N/A"
    items_str = extracted.items_readable() or "None"

    return (
        f"⚠️ *Munim AI Owner Alert*\n\n"
        f"Customer: +{extracted.customer_phone} ({extracted.customer_name or 'Unknown'})\n"
        f"Type: {extracted.type.upper()}\n"
        f"Reason: {reason}\n"
        f"Confidence: {int(extracted.confidence.overall * 100)}%\n"
        f"Amount: {amt_str}\n"
        f"Items: {items_str}\n\n"
        f"Reply '#confirm' to accept or '#reject' to decline."
    )

