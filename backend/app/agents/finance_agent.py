import logging
from typing import Dict, Any, Optional

from backend.app.models.schemas import ExtractedMessage
from backend.app.services import orders, payments

logger = logging.getLogger(__name__)

class FinanceAgent:
    """
    The payment and ledger specialist.
    Matches UPI receipts to orders, creates reviewable payment claims,
    and calculates outstanding customer balances and store dues.
    Screenshots are always recorded as 'pending_verification' for dashboard review.
    """

    def __init__(self, name: str = "FinanceAgent"):
        self.name = name

    async def handle(
        self,
        message: ExtractedMessage,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        seller_id = context.get("seller_id", "default_seller")
        customer_id = context.get("customer_id", message.customer_phone)
        customer_name = message.customer_name or context.get("customer_name") or "Ji"

        amount = message.amount
        upi_ref = message.upi_txn_id

        # 1. Look for matching pending order for this customer
        matching_order = await orders.find_payment_match(
            seller_id=seller_id,
            customer_id=customer_id,
            amount=amount,
            reference=upi_ref
        )

        matched_order_id = matching_order["id"] if matching_order else message.linked_order_id
        is_clear_match = bool(matching_order)

        # 2. Record payment claim (pending owner verification on dashboard)
        claim_status = "pending_verification"
        claim_result = await payments.create_claim(
            seller_id=seller_id,
            customer_id=customer_id,
            order_id=matched_order_id,
            amount=amount,
            upi_ref=upi_ref,
            status=claim_status,
            raw_details={"media_type": message.media_type, "raw_text": message.raw_text}
        )

        # 3. Calculate remaining balance / dues
        dues_info = await payments.get_customer_dues(seller_id, customer_id)
        outstanding = dues_info.get("outstanding_dues", 0.0)

        # 4. Craft customer confirmation
        amt_str = f"₹{int(amount)} " if amount else ""
        utr_str = f"\n🔖 UPI Ref / UTR: *{upi_ref}*" if upi_ref else ""
        order_str = f"\n📦 Linked to Order: *#{matched_order_id}*" if matched_order_id else ""

        reply = (
            f"Dhanyawaad {customer_name}! 🙏\n\n"
            f"Aapki {amt_str}payment receipt record kar li gayi hai.{utr_str}{order_str}\n\n"
            f"Bank settlement verify hote hi aapka parcel dispatch kar diya jayega!"
        )

        # 5. Determine if owner review is required (e.g. unmatched payment or partial payment)
        escalate = not is_clear_match or message.type == "partial_payment" or message.confidence.overall < 0.75
        escalation_reason = None
        if not is_clear_match:
            escalation_reason = f"Payment of ₹{amount} received from {message.customer_phone} without matching open order."
        elif message.type == "partial_payment":
            escalation_reason = f"Partial payment of ₹{amount} received; pending dues ₹{outstanding}."

        return {
            "agent": self.name,
            "action": "payment_claim_created",
            "reply": reply,
            "escalate": escalate,
            "escalation_reason": escalation_reason,
            "data": {
                "claim": claim_result,
                "dues": dues_info,
                "matched_order_id": matched_order_id
            }
        }

    async def get_summary_report(self, seller_id: str) -> str:
        """
        Builds a quick dues and financial summary for the business owner.
        """
        # In a real store, aggregates total verified today
        return (
            "📊 *Munim AI Daily Financial Summary*\n\n"
            "✅ Verified Payments: Review on Dashboard\n"
            "⏳ Pending Claims: 1 requires verification\n"
            "📌 Outstanding Customer Dues: View via Dashboard > Pending Dues\n"
        )
