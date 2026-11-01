import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.order import (
    OrderCreateRequest,
    OrderResponse,
    OrderItemResponse,
)
from backend.app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


@router.get("", response_model=List[OrderResponse])
async def list_orders(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter orders by status"),
    customer_id: Optional[UUID] = Query(default=None, description="Filter orders by customer UUID"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of orders to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[OrderResponse]:
    """Retrieve orders for the authenticated seller with optional filters."""
    service = OrderService(seller.db)
    orders = service.list_orders(
        seller_id=seller.id,
        status=status_filter,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )
    return [OrderResponse.model_validate(o) for o in orders]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> OrderResponse:
    """
    Create a new order with atomic stock reservation using PostgreSQL RPC.
    - Server-authoritative pricing directly from database variants.
    - Atomic inventory reservation.
    - Full transaction rollback on validation or stock failure.
    """
    service = OrderService(seller.db)
    order = service.create_order_with_reservation(seller_id=seller.id, data=payload)
    return OrderResponse.model_validate(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> OrderResponse:
    """Retrieve a single order by ID, strictly scoped to the authenticated seller."""
    service = OrderService(seller.db)
    order = service.get_order(seller_id=seller.id, order_id=order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )
    return OrderResponse.model_validate(order)


@router.get("/{order_id}/items", response_model=List[OrderItemResponse])
async def get_order_items(
    order_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[OrderItemResponse]:
    """Retrieve all line items for an order owned by the authenticated seller."""
    service = OrderService(seller.db)
    items = service.get_order_items(seller_id=seller.id, order_id=order_id)
    return [OrderItemResponse.model_validate(it) for it in items]


@router.post("/{order_id}/fulfill", response_model=OrderResponse)
async def fulfill_order(
    order_id: UUID,
    target_status: str = Query(default="delivered", description="Target fulfillment status: delivered or shipped"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> OrderResponse:
    """
    Atomically fulfill an order using PostgreSQL RPC:
    - Decrements physical stock and clears reservation.
    - Transitions order status to target_status.
    - Rejects duplicate or partial fulfillment.
    """
    service = OrderService(seller.db)
    order = service.fulfill_order(seller_id=seller.id, order_id=order_id, target_status=target_status)
    return OrderResponse.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> OrderResponse:
    """
    Atomically cancel an order using PostgreSQL RPC:
    - Releases reserved stock without mutating physical stock.
    - Transitions order status to 'cancelled'.
    - Preserves historical line items.
    """
    service = OrderService(seller.db)
    order = service.cancel_order(seller_id=seller.id, order_id=order_id)
    return OrderResponse.model_validate(order)

