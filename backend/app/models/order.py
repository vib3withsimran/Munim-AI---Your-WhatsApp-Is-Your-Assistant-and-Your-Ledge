from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class OrderItem(BaseModel):
    """Domain model representing a row in the Supabase 'order_items' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique order item identifier (UUID)")
    order_id: UUID = Field(description="Foreign key referencing orders.id")
    seller_id: UUID = Field(description="Tenant seller ID owning this order item")
    variant_id: UUID = Field(description="Foreign key referencing product_variants.id")
    quantity: int = Field(description="Quantity ordered", ge=1)
    unit_price: Decimal = Field(description="Snapshot unit price at time of order creation", ge=Decimal("0.00"))
    line_total: Decimal = Field(description="Line total (quantity * unit_price)", ge=Decimal("0.00"))
    product_name_snapshot: Optional[str] = Field(default=None, description="Snapshot product title at order time")
    variant_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot variant details (size, color, SKU) as JSONB")


class Order(BaseModel):
    """Domain model representing a row in the Supabase 'orders' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique order identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this order")
    customer_id: UUID = Field(description="Foreign key referencing customers.id")
    status: str = Field(description="Order lifecycle status (e.g. pending, processing, completed, cancelled)")
    total_amount: Decimal = Field(description="Server-calculated total order amount as Decimal", ge=Decimal("0.00"))
    currency: str = Field(default="INR", description="Three-letter currency code (ISO 4217)")
    notes: Optional[str] = Field(default=None, description="Optional merchant notes or customer instructions")
    created_at: datetime = Field(description="Timestamp when order was placed")
    updated_at: datetime = Field(description="Timestamp when order was last updated")
    items: Optional[List[OrderItem]] = Field(default=None, description="Optional list of associated order items")


