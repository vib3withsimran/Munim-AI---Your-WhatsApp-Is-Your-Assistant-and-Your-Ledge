import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.models.dashboard_schemas import (
    DashboardSummaryResponse,
    DashboardSalesResponse,
    DashboardActivityResponse,
    DashboardBreakdownResponse,
)
from backend.app.services.dashboard_service import (
    get_dashboard_summary,
    get_dashboard_sales,
    get_dashboard_activity,
    get_dashboard_breakdown,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

VALID_PERIODS = {"7D", "30D", "3M", "6M"}


@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> DashboardSummaryResponse:
    """
    Retrieve aggregated dashboard summary metrics:
    - Monthly revenue (verified payments received this calendar month, excluding cancelled orders).
    - Total orders (all non-cancelled orders).
    - Active customers (distinct buyers with orders).
    - Outstanding dues (order total minus verified payments; unverified/rejected payments do not reduce dues).
    """
    try:
        return get_dashboard_summary(seller.id, seller.db)
    except Exception as e:
        logger.error(f"Error fetching dashboard summary for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute dashboard summary metrics."
        )


@router.get("/sales", response_model=DashboardSalesResponse)
async def dashboard_sales(
    period: str = Query(default="30D", description="Time period filter: 7D, 30D, 3M, 6M"),
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> DashboardSalesResponse:
    """
    Retrieve date-wise sales totals for SalesChart and SplineChart.
    Validates period parameter (7D, 30D, 3M, 6M).
    Uses dynamic UTC timestamps to aggregate verified payments.
    """
    period_upper = period.upper().strip()
    if period_upper not in VALID_PERIODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period '{period}'. Supported periods: 7D, 30D, 3M, 6M."
        )

    try:
        return get_dashboard_sales(seller.id, period_upper, seller.db)
    except Exception as e:
        logger.error(f"Error fetching dashboard sales for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute sales overview data."
        )


@router.get("/activity", response_model=DashboardActivityResponse)
async def dashboard_activity(
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> DashboardActivityResponse:
    """
    Retrieve genuine today's activity counts and Meko memory highlights.
    Returns actual counts from orders, payments, and agent_logs.
    If Meko memory highlights are not available, returns an empty array.
    """
    try:
        return get_dashboard_activity(seller.id, seller.db)
    except Exception as e:
        logger.error(f"Error fetching dashboard activity for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity and memory data."
        )


@router.get("/breakdown", response_model=DashboardBreakdownResponse)
async def dashboard_breakdown(
    seller: AuthenticatedSeller = Depends(get_current_seller)
) -> DashboardBreakdownResponse:
    """
    Retrieve bottom section breakdown:
    - Order counts by status with theme color assignments.
    - Top selling products based on order_items snapshots.
    - Customers with outstanding pending dues.
    """
    try:
        return get_dashboard_breakdown(seller.id, seller.db)
    except Exception as e:
        logger.error(f"Error fetching dashboard breakdown for seller {seller.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard breakdown data."
        )


@router.post("/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: str,
    seller: AuthenticatedSeller = Depends(get_current_seller)
):
    """
    Approves a pending payment claim:
    1. Sets payment status to verified in Supabase.
    2. Enqueues outbound confirmation to customer on WhatsApp via Phase 5 DurableQueue.
    """
    try:
        from backend.app.services.payments import approve_payment_claim
        from backend.app.queue import get_durable_queue, JobType

        res = await approve_payment_claim(seller.id, payment_id)
        customer_phone = res.get("customer_phone")
        if customer_phone:
            q = get_durable_queue()
            q.enqueue(JobType.PAYMENT_APPROVED_ALERT, {
                "to_phone": customer_phone,
                "amount": res.get("amount", 0.0),
                "order_id": res.get("order_id")
            })
            logger.info(f"Enqueued PAYMENT_APPROVED_ALERT to {customer_phone} for payment {payment_id}")

        return {"status": "success", "message": f"Payment {payment_id} approved.", "details": res}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error approving payment {payment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve payment claim.")


@router.post("/payments/{payment_id}/reject")
async def reject_payment(
    payment_id: str,
    reason: str = Query(default="Payment verification failed"),
    seller: AuthenticatedSeller = Depends(get_current_seller)
):
    """Rejects an unverified payment claim."""
    try:
        from backend.app.services.payments import reject_payment_claim
        res = await reject_payment_claim(seller.id, payment_id, reason=reason)
        return {"status": "success", "message": f"Payment {payment_id} rejected.", "details": res}
    except Exception as e:
        logger.error(f"Error rejecting payment {payment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject payment claim.")
