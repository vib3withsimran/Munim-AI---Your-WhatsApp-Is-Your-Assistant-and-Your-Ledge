import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductVariantCreateRequest,
    ProductVariantResponse,
)
from backend.app.services.product_service import ProductService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
async def list_products(
    is_active: Optional[bool] = Query(default=None, description="Filter products by active status"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of products to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[ProductResponse]:
    """Retrieve catalog products for the authenticated seller."""
    service = ProductService(seller.db)
    products = service.list_products(seller_id=seller.id, is_active=is_active, limit=limit, offset=offset)
    return [ProductResponse.model_validate(p) for p in products]


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> ProductResponse:
    """Create a new product under the authenticated seller."""
    service = ProductService(seller.db)
    product = service.create_product(seller_id=seller.id, data=payload)
    return ProductResponse.model_validate(product)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> ProductResponse:
    """Retrieve a single product by ID, strictly scoped to the authenticated seller."""
    service = ProductService(seller.db)
    product = service.get_product(seller_id=seller.id, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )
    return ProductResponse.model_validate(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> ProductResponse:
    """Update details of an existing product owned by the authenticated seller."""
    service = ProductService(seller.db)
    product = service.update_product(seller_id=seller.id, product_id=product_id, data=payload)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}")
async def archive_product(
    product_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> Dict[str, Any]:
    """Soft-delete / archive a product owned by the authenticated seller."""
    service = ProductService(seller.db)
    service.archive_product(seller_id=seller.id, product_id=product_id)
    return {"success": True, "message": f"Product '{product_id}' archived successfully"}


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    product_id: UUID,
    payload: ProductVariantCreateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> ProductVariantResponse:
    """Create a variant under a parent product owned by the authenticated seller."""
    if payload.product_id is not None and payload.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"product_id in body ('{payload.product_id}') must match URL path ('{product_id}')",
        )
    data = payload.model_copy(update={"product_id": product_id})
    service = ProductService(seller.db)
    variant = service.create_variant(seller_id=seller.id, data=data)
    return ProductVariantResponse.model_validate(variant)


@router.get("/{product_id}/variants", response_model=List[ProductVariantResponse])
async def list_variants(
    product_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[ProductVariantResponse]:
    """Retrieve all variants for a product owned by the authenticated seller."""
    service = ProductService(seller.db)
    variants = service.list_variants(seller_id=seller.id, product_id=product_id)
    return [ProductVariantResponse.model_validate(v) for v in variants]

