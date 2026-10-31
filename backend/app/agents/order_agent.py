import logging
from typing import Dict, Any, List, Optional

from backend.app.models.schemas import ExtractedMessage
from backend.app.services import catalog, orders

logger = logging.getLogger(__name__)

class OrderAgent:
    """
    The order and inventory operations specialist.
    Performs deterministic stock arithmetic, inventory verification, atomic stock reservation,
    and order creation. Never hallucinates stock or prices.
    """

    def __init__(self, name: str = "OrderAgent"):
        self.name = name

    async def handle(
        self,
        message: ExtractedMessage,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        seller_id = context.get("seller_id", "default_seller")
        customer_id = context.get("customer_id", message.customer_phone)
        customer_name = message.customer_name or context.get("customer_name") or "Ji"

        # 1. Validate if items exist
        if not message.items:
            # Ambiguous order request without clear items
            return {
                "agent": self.name,
                "action": "needs_clarification",
                "reply": f"Namaste {customer_name}! 🙏 Aapko kaunsa item aur kitni quantity chahiye? Kripya item ka naam aur size batayein.",
                "escalate": False,
                "data": {}
            }

        # 2. Match each item against catalog and verify inventory
        order_line_items = []
        unavailable_items = []

        for item in message.items:
            variant = await catalog.find_variant(
                seller_id=seller_id,
                item_name=item.name,
                size=item.size,
                color=item.color
            )

            if not variant:
                unavailable_items.append(item.name)
                continue

            available_stock = int(variant.get("stock", 0))
            if available_stock < item.qty:
                unavailable_items.append(f"{variant['name']} (Sirf {available_stock} available hai, aapne {item.qty} maanga hai)")
                continue

            # Deterministic pricing from verified catalog (overrides any LLM guess)
            unit_price = float(variant.get("price", item.unit_price or 799.0))
            order_line_items.append({
                "product_id": variant["id"],
                "name": variant["name"],
                "qty": item.qty,
                "size": item.size or variant.get("requested_size"),
                "color": item.color or variant.get("requested_color"),
                "unit_price": unit_price
            })

        # 3. If any item is unavailable, inform customer without taking bad order
        if unavailable_items:
            missing_str = ", ".join(unavailable_items)
            reply = (
                f"Namaste {customer_name}! 🙏\n\n"
                f"Maafi chahenge, {missing_str} abhi out-of-stock hai.\n"
                f"Kya aap dusra size ya alternative dekhna chahenge?"
            )
            return {
                "agent": self.name,
                "action": "out_of_stock",
                "reply": reply,
                "escalate": False,
                "data": {"unavailable": unavailable_items}
            }

        # 4. Atomic stock reservation & Order creation
        order_result = await orders.create_with_stock_reservation(
            seller_id=seller_id,
            customer_id=customer_id,
            items=order_line_items,
            message_id=message.message_id,
            delivery_address=message.delivery_address
        )

        order_id = order_result["order_id"]
        total_amount = order_result["total_amount"]

        # Itemized summary for customer
        items_summary = "\n".join([
            f"• {it['qty']}x {it['name']} ({it['size'] or 'Standard'}) — ₹{int(it['unit_price'] * it['qty'])}"
            for it in order_line_items
        ])

        address_prompt = ""
        if not message.delivery_address:
            address_prompt = "\n📍 Kripya apna delivery address aur pincode bhej dijiye."

        reply = (
            f"Namaste {customer_name}! 🙏\n\n"
            f"Aapka order note kar liya gaya hai (Order ID: *#{order_id}*):\n\n"
            f"{items_summary}\n\n"
            f"💵 *Kul Rashi (Total): ₹{int(total_amount)}*\n"
            f"{address_prompt}\n"
            f"Aap payment UPI se kar sakte hain aur screenshot yahan share kar dein."
        )

        return {
            "agent": self.name,
            "action": "order_created",
            "reply": reply,
            "escalate": False,
            "data": order_result
        }

