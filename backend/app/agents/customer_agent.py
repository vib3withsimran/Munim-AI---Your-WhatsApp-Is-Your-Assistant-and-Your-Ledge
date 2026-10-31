import logging
from typing import Dict, Any, List, Optional

from backend.app.models.schemas import ExtractedMessage
from backend.app.services import catalog, orders
from backend.app.ai.response_generator import generate_smart_reply

logger = logging.getLogger(__name__)

STORE_POLICIES = {
    "exchange": "7 din ke andar size exchange available hai, tag intact hona chahiye.",
    "delivery": "Delivery all-India available hai. NCR mein 2-3 din, baaki states mein 4-6 din.",
    "payment_methods": "UPI (Google Pay, PhonePe, Paytm, BHIM) and Cash on Delivery (COD) available.",
    "return": "Damaged pieces par 100% refund ya replacement milta hai parcel opening video ke saath."
}

class CustomerAgent:
    """
    The conversation and customer relationship specialist.
    Handles catalog questions, sizes, prices, availability, delivery tracking, policies, and FAQs.
    Does NOT mutate inventory or record financial claims directly.
    """

    def __init__(self, name: str = "CustomerAgent"):
        self.name = name

    async def handle(
        self,
        message: ExtractedMessage,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        seller_id = context.get("seller_id", "default_seller")
        customer_id = context.get("customer_id", message.customer_phone)
        customer_name = message.customer_name or context.get("customer_name") or "Ji"

        msg_type = message.type

        # 1. Catalog / Product Inquiry
        if msg_type in ["catalog_query", "question"] and any(w in message.raw_text.lower() for w in ["kurti", "size", "rate", "price", "catalog", "suit", "stock", "available", "dikhao"]):
            # Search active products
            matched_products = await catalog.search(seller_id=seller_id, query=message.raw_text)
            if matched_products:
                top_items = matched_products[:3]
                items_text = "\n".join([
                    f"• *{p['name']}*: ₹{int(p['price'])} ({p.get('description', 'All sizes available')})"
                    for p in top_items
                ])
                reply = (
                    f"Namaste {customer_name}! 🙏\n\n"
                    f"Haanji! Hamare paas ye collection available hai:\n\n"
                    f"{items_text}\n\n"
                    f"Aapko kaunsa size (S, M, L, XL, XXL) ya color pack karwana hai?"
                )
                return {
                    "agent": self.name,
                    "action": "catalog_replied",
                    "reply": reply,
                    "escalate": False,
                    "data": {"products": matched_products}
                }

        # 2. Delivery / Order Tracking Inquiry
        if msg_type == "delivery_query" or any(w in message.raw_text.lower() for w in ["parcel", "delivery", "track", "dispatch", "kahan pahucha", "kab aayega"]):
            cust_orders = await orders.get_customer_orders(seller_id, customer_id)
            if cust_orders:
                latest = cust_orders[0]
                status_txt = latest.get("status", "processing").replace("_", " ").title()
                reply = (
                    f"Namaste {customer_name}! 🙏\n\n"
                    f"Aapka order (#{latest['id']}) abhi *{status_txt}* status par hai.\n"
                    f"Total amount: ₹{int(latest.get('total_amount', 0))}.\n"
                    f"Dispatch update aur tracking link jald hi WhatsApp par share kar diya jayega!"
                )
            else:
                reply = (
                    f"Namaste {customer_name}! 🙏\n\n"
                    f"{STORE_POLICIES['delivery']}\n"
                    f"Agar aapne order book kiya hai toh kripya apna order number ya registered number share karein."
                )
            return {
                "agent": self.name,
                "action": "delivery_status_replied",
                "reply": reply,
                "escalate": False,
                "data": {"orders": cust_orders}
            }

        # 3. Policy or FAQ Inquiry (Exchange / Return / Payment methods)
        lower_txt = message.raw_text.lower()
        if "exchange" in lower_txt or "badal" in lower_txt or "return" in lower_txt:
            reply = f"Namaste {customer_name}! 🙏\n\n{STORE_POLICIES['exchange']}\n{STORE_POLICIES['return']}"
            return {
                "agent": self.name,
                "action": "policy_replied",
                "reply": reply,
                "escalate": False,
                "data": {}
            }

        # 4. Complaint / Ambiguous request -> Escalate to Owner
        if msg_type == "complaint" or message.confidence.overall < 0.70:
            reply = (
                f"Namaste {customer_name}! 🙏\n\n"
                f"Humein khed hai ki aapko pareshani hui. Maine store owner ko ye message notify kar diya hai. "
                f"Vo personally aapse jaldi contact karenge."
            )
            return {
                "agent": self.name,
                "action": "escalated_to_owner",
                "reply": reply,
                "escalate": True,
                "escalation_reason": message.escalation_reason or "Customer complaint or low confidence query."
            }

        # 5. Default natural conversational fallback
        fallback_reply = generate_smart_reply(message)
        return {
            "agent": self.name,
            "action": "general_reply",
            "reply": fallback_reply,
            "escalate": False,
            "data": {}
        }
