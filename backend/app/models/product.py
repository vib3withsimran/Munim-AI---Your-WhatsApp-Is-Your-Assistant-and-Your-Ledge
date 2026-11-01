from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Product(BaseModel):
    """Domain model representing a row in the Supabase 'products' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique product identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this product")
    name: str = Field(description="Product title / name")
    description: Optional[str] = Field(default=None, description="Detailed product description")
    category: Optional[str] = Field(default=None, description="Product category or collection")
    image_path: Optional[str] = Field(default=None, description="Relative storage path or filename of product image")
    is_active: bool = Field(default=True, description="Whether product is active in the catalog")
    created_at: datetime = Field(description="Timestamp when product was created")


class ProductVariant(BaseModel):
    """Domain model representing a row in the Supabase 'product_variants' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique variant identifier (UUID)")
    product_id: UUID = Field(description="Foreign key referencing products.id")
    seller_id: UUID = Field(description="Tenant seller ID owning this variant")
    sku: Optional[str] = Field(default=None, description="Stock Keeping Unit / variant code")
    size: Optional[str] = Field(default=None, description="Variant size (e.g. S, M, L, XL)")
    color: Optional[str] = Field(default=None, description="Variant color (e.g. Blue, Red)")
    price: Decimal = Field(description="Authoritative unit selling price in INR as Decimal", ge=Decimal("0.00"))
    created_at: datetime = Field(description="Timestamp when variant was created")

