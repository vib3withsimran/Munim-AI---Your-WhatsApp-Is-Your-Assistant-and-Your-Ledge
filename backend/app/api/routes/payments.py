import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.payment import (
    PaymentCreateRequest,
    PaymentLinkRequest,
    PaymentResponse,
)
from backend.app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter payments by status"),
    order_id: Optional[UUID] = Query(default=None, description="Filter payments by order UUID"),
    unlinked_only: bool = Query(default=False, description="Filter only unlinked payments (order_id is null)"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of payments to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[PaymentResponse]:
    """Retrieve payments for the authenticated seller with optional filters."""
    service = PaymentService(seller.db)
    payments = service.list_payments(
        seller_id=seller.id,
        status=status_filter,
        order_id=order_id,
        unlinked_only=unlinked_only,
        limit=limit,
        offset=offset,
    )
    return [PaymentResponse.model_validate(p) for p in payments]


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payload: PaymentCreateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> PaymentResponse:
    """Record a new payment under the authenticated seller."""
    service = PaymentService(seller.db)
    payment = service.record_payment(seller_id=seller.id, data=payload, is_owner_action=True)
    return PaymentResponse.model_validate(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> PaymentResponse:
    """Retrieve a single payment by ID, strictly scoped to the authenticated seller."""
    service = PaymentService(seller.db)
    payment = service.get_payment(seller_id=seller.id, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment '{payment_id}' not found",
        )
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/verify", response_model=PaymentResponse)
async def verify_payment(
    payment_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> PaymentResponse:
    """Explicitly verify a payment as the authenticated seller."""
    service = PaymentService(seller.db)
    payment = service.verify_payment(seller_id=seller.id, payment_id=payment_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/reject", response_model=PaymentResponse)
async def reject_payment(
    payment_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> PaymentResponse:
    """Explicitly reject a payment as the authenticated seller."""
    service = PaymentService(seller.db)
    payment = service.reject_payment(seller_id=seller.id, payment_id=payment_id)
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/link", response_model=PaymentResponse)
async def link_payment(
    payment_id: UUID,
    payload: PaymentLinkRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> PaymentResponse:
    """Explicitly link an unlinked payment to an eligible order after merchant review."""
    service = PaymentService(seller.db)
    payment = service.link_payment_to_order(
        seller_id=seller.id,
        payment_id=payment_id,
        order_id=payload.order_id,
        is_owner_action=True,
    )
    return PaymentResponse.model_validate(payment)

