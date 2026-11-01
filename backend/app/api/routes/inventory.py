import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.inventory import (
    InventoryUpdateRequest,
    InventoryResponse,
)
from backend.app.services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("", response_model=List[InventoryResponse])
async def list_inventory(
    low_stock_only: bool = Query(default=False, description="Filter only records where available <= threshold"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of inventory records to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[InventoryResponse]:
    """Retrieve inventory stock records for the authenticated seller."""
    service = InventoryService(seller.db)
    records = service.list_inventory(seller_id=seller.id, low_stock_only=low_stock_only, limit=limit, offset=offset)
    return [InventoryResponse.model_validate(r) for r in records]


@router.get("/{variant_id}", response_model=InventoryResponse)
async def get_inventory(
    variant_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> InventoryResponse:
    """Retrieve inventory for a specific variant owned by the authenticated seller."""
    service = InventoryService(seller.db)
    record = service.get_inventory(seller_id=seller.id, variant_id=variant_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record for variant '{variant_id}' not found",
        )
    return InventoryResponse.model_validate(record)


@router.patch("/{variant_id}", response_model=InventoryResponse)
async def update_inventory(
    variant_id: UUID,
    payload: InventoryUpdateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> InventoryResponse:
    """Update stock levels or threshold for a variant owned by the authenticated seller."""
    service = InventoryService(seller.db)
    record = service.update_inventory(seller_id=seller.id, variant_id=variant_id, data=payload)
    return InventoryResponse.model_validate(record)

