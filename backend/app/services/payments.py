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


async def approve_payment_claim(seller_id: str, payment_id: str) -> Dict[str, Any]:
    """
    Approves a pending payment claim:
    1. Updates payment status to 'verified' in Supabase.
    2. Updates linked order status to 'completed' or 'paid'.
    3. Returns customer details for sending outbound notification.
    """
    supabase = get_supabase_client()
    # Fetch payment
    p_res = supabase.table("payments").select("*").eq("id", payment_id).eq("seller_id", seller_id).execute()
    payments = p_res.data or []
    if not payments:
        raise ValueError(f"Payment claim {payment_id} not found.")

    payment = payments[0]
    supabase.table("payments").update({"status": "verified"}).eq("id", payment_id).execute()

    order_id = payment.get("order_id")
    customer_phone = None
    if order_id:
        supabase.table("orders").update({"status": "completed"}).eq("id", order_id).execute()
        o_res = supabase.table("orders").select("customer_id").eq("id", order_id).execute()
        if o_res.data:
            cust_id = o_res.data[0].get("customer_id")
            if cust_id:
                c_res = supabase.table("customers").select("phone").eq("id", cust_id).execute()
                if c_res.data:
                    customer_phone = c_res.data[0].get("phone")

    return {
        "success": True,
        "payment_id": payment_id,
        "amount": payment.get("amount", 0.0),
        "order_id": order_id,
        "customer_phone": customer_phone
    }


async def reject_payment_claim(seller_id: str, payment_id: str, reason: str = "Payment verification failed") -> Dict[str, Any]:
    """Rejects an unverified payment claim."""
    supabase = get_supabase_client()
    supabase.table("payments").update({"status": "rejected"}).eq("id", payment_id).eq("seller_id", seller_id).execute()
    return {"success": True, "payment_id": payment_id, "status": "rejected", "reason": reason}
