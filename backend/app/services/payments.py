import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from backend.app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

async def create_claim(
    seller_id: str,
    customer_id: str,
    order_id: Optional[str] = None,
    amount: Optional[float] = None,
    upi_ref: Optional[str] = None,
    status: str = "pending_verification",
    raw_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Records a payment claim extracted from customer messages or UPI screenshots.
    Never marks payment as fully verified automatically; records as pending_verification for seller dashboard confirmation.
    """
    payment_uuid = str(uuid.uuid4())
    display_payment_id = f"PAY-{payment_uuid[:6].upper()}"
    claim_amount = float(amount) if amount is not None else 0.0

    payment_record = {
        "id": payment_uuid,
        "seller_id": seller_id,
        "order_id": order_id if (order_id and len(order_id) == 36) else None,
        "amount": claim_amount,
        "status": status,
        "created_at": datetime.now().isoformat()
    }

    try:
        supabase = get_supabase_client()
        supabase.table("payments").insert(payment_record).execute()

        # If linked to order and status is verified, update order status
        if order_id and status == "verified":
            supabase.table("orders").update({"status": "completed"}).eq("id", order_id).execute()

    except Exception as e:
        logger.warning(f"Could not persist payment claim to Supabase ({e})")

    return {
        "status": "success",
        "payment_id": display_payment_id,
        "payment_uuid": payment_uuid,
        "amount": claim_amount,
        "order_id": order_id,
        "upi_ref": upi_ref,
        "claim_status": status
    }


async def get_customer_dues(seller_id: str, customer_id: str) -> Dict[str, Any]:
    """
    Calculates outstanding dues deterministically:
    Total amount of uncancelled orders minus verified payments.
    """
    try:
        supabase = get_supabase_client()
        # Fetch non-cancelled orders for this customer
        orders_res = (
            supabase.table("orders")
            .select("id, total_amount, status")
            .eq("seller_id", seller_id)
            .eq("customer_id", customer_id)
            .execute()
        )
        orders = orders_res.data or []
        non_cancelled_orders = [o for o in orders if str(o.get("status", "")).lower() not in ("cancelled", "canceled")]
        total_ordered = sum(float(o.get("total_amount", 0)) for o in non_cancelled_orders)
        order_ids = [str(o["id"]) for o in non_cancelled_orders]

        # Fetch verified payments linked to these orders
        total_paid = 0.0
        if order_ids:
            payments_res = (
                supabase.table("payments")
                .select("amount, status, order_id")
                .eq("seller_id", seller_id)
                .in_("order_id", order_ids)
                .eq("status", "verified")
                .execute()
            )
            payments = payments_res.data or []
            total_paid = sum(float(p.get("amount", 0)) for p in payments)

        outstanding = max(0.0, total_ordered - total_paid)
        return {
            "total_ordered": total_ordered,
            "total_paid": total_paid,
            "outstanding_dues": outstanding
        }
    except Exception as e:
        logger.warning(f"Error calculating dues: {e}")
        return {
            "total_ordered": 0.0,
            "total_paid": 0.0,
            "outstanding_dues": 0.0
        }
