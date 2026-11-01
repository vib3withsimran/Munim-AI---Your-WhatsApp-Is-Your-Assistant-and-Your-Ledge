import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.customer import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerResponse,
)
from backend.app.services.customer_service import CustomerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of customers to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> List[CustomerResponse]:
    """Retrieve customers for the authenticated seller with pagination."""
    service = CustomerService(seller.db)
    customers = service.list_customers(seller_id=seller.id, limit=limit, offset=offset)
    return [CustomerResponse.model_validate(c) for c in customers]


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> CustomerResponse:
    """Create a new customer under the authenticated seller."""
    service = CustomerService(seller.db)
    customer = service.create_customer(seller_id=seller.id, data=payload)
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> CustomerResponse:
    """Retrieve a single customer by ID, enforcing seller ownership."""
    service = CustomerService(seller.db)
    customer = service.get_customer(seller_id=seller.id, customer_id=customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found",
        )
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdateRequest,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> CustomerResponse:
    """Update details of an existing customer owned by the authenticated seller."""
    service = CustomerService(seller.db)
    customer = service.update_customer(seller_id=seller.id, customer_id=customer_id, data=payload)
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
) -> Dict[str, Any]:
    """Safely archive or delete a customer owned by the authenticated seller."""
    service = CustomerService(seller.db)
    service.archive_customer(seller_id=seller.id, customer_id=customer_id)
    return {"success": True, "message": f"Customer '{customer_id}' archived successfully"}

