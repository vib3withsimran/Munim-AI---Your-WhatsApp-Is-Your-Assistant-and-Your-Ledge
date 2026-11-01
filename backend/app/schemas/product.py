from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductCreateRequest(BaseModel):
    """Payload to create a new product. Seller ownership is derived from JWT context."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200, description="Product title / name (required, non-empty)")
    description: Optional[str] = Field(default=None, max_length=2000, description="Detailed product description")
    category: Optional[str] = Field(default=None, max_length=100, description="Product category or collection")
    image_path: Optional[str] = Field(default=None, max_length=500, description="Storage path or filename of product image")
    is_active: bool = Field(default=True, description="Whether product is active in catalog")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Product name cannot be empty or whitespace only")
        return stripped


class ProductUpdateRequest(BaseModel):
    """Payload to update an existing product."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Updated product name")
    description: Optional[str] = Field(default=None, max_length=2000, description="Updated description")
    category: Optional[str] = Field(default=None, max_length=100, description="Updated category")
    image_path: Optional[str] = Field(default=None, max_length=500, description="Updated image path")
    is_active: Optional[bool] = Field(default=None, description="Updated active status")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Product name cannot be empty or whitespace only")
            return stripped
        return None


class ProductResponse(BaseModel):
    """Product representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique product identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this product")
    name: str = Field(description="Product name")
    description: Optional[str] = Field(default=None, description="Product description")
    category: Optional[str] = Field(default=None, description="Product category")
    image_path: Optional[str] = Field(default=None, description="Image storage path")
    is_active: bool = Field(description="Whether product is active")
    created_at: datetime = Field(description="Timestamp when product was created")


class ProductVariantCreateRequest(BaseModel):
    """Payload to create a new product variant."""

    model_config = ConfigDict(extra="forbid")

    product_id: Optional[UUID] = Field(default=None, description="UUID of the parent product")
    sku: Optional[str] = Field(default=None, max_length=100, description="Stock Keeping Unit / code")
    size: Optional[str] = Field(default=None, max_length=50, description="Size specification (e.g. S, M, L, XL)")
    color: Optional[str] = Field(default=None, max_length=50, description="Color specification (e.g. Blue, Maroon)")
    price: Decimal = Field(..., ge=Decimal("0.00"), description="Unit price in INR as non-negative Decimal")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError("Price cannot be negative")
        return round(v, 2)


class ProductVariantUpdateRequest(BaseModel):
    """Payload to update an existing product variant."""

    model_config = ConfigDict(extra="forbid")

    sku: Optional[str] = Field(default=None, max_length=100, description="Updated SKU")
    size: Optional[str] = Field(default=None, max_length=50, description="Updated size")
    color: Optional[str] = Field(default=None, max_length=50, description="Updated color")
    price: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Updated price as Decimal")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            if v < Decimal("0.00"):
                raise ValueError("Price cannot be negative")
            return round(v, 2)
        return None


class ProductVariantResponse(BaseModel):
    """Product variant representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique variant identifier (UUID)")
    product_id: UUID = Field(description="Parent product UUID")
    seller_id: UUID = Field(description="Tenant seller ID owning this variant")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit")
    size: Optional[str] = Field(default=None, description="Size")
    color: Optional[str] = Field(default=None, description="Color")
    price: Decimal = Field(description="Authoritative price as Decimal")
    created_at: datetime = Field(description="Timestamp when variant was created")


class ProductWithVariantsResponse(ProductResponse):
    """Composite product response including nested variants."""

    variants: List[ProductVariantResponse] = Field(default_factory=list, description="List of variants for this product")
