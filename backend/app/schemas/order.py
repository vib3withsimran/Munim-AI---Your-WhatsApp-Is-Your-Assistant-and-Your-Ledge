from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(str, Enum):
    """Supported order lifecycle statuses aligned with business workflows."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    COMPLETED = "completed"  # Backward compatibility with existing records


class OrderItemCreateRequest(BaseModel):
    """Line item requested for order creation. Pricing is strictly calculated server-side."""

    model_config = ConfigDict(extra="forbid")

    variant_id: UUID = Field(description="UUID of the product variant being ordered")
    quantity: int = Field(default=1, ge=1, description="Quantity to order (must be positive integer)")

    @field_validator("quantity")
    @classmethod
    def validate_positive_quantity(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Order item quantity must be at least 1")
        return v


class OrderItemResponse(BaseModel):
    """Line item representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique order item identifier (UUID)")
    order_id: UUID = Field(description="Parent order UUID")
    seller_id: UUID = Field(description="Tenant seller ID")
    variant_id: UUID = Field(description="Product variant UUID")
    quantity: int = Field(description="Quantity ordered")
    unit_price: Decimal = Field(description="Authoritative unit price snapshot")
    line_total: Decimal = Field(description="Calculated line total")
    product_name_snapshot: Optional[str] = Field(default=None, description="Snapshot product title")
    variant_snapshot: Optional[Dict[str, Any]] = Field(default=None, description="Snapshot variant details as JSONB")


class OrderCreateRequest(BaseModel):
    """
    Payload to place a new order.
    Total amount is strictly calculated by the server using current variant prices.
    Frontend-calculated totals are rejected.
    """

    model_config = ConfigDict(extra="forbid")

    customer_id: UUID = Field(description="Customer UUID placing the order")
    items: List[OrderItemCreateRequest] = Field(..., min_length=1, description="List of items ordered (at least 1 required)")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="Three-letter ISO currency code (default: INR)")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Optional order notes or instructions")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("Currency must be a valid 3-letter ISO alphabetical code (e.g. INR)")
        return cleaned


class OrderStatusUpdateRequest(BaseModel):
    """Payload to transition order lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    status: OrderStatus = Field(description="Target order lifecycle status")


class OrderResponse(BaseModel):
    """Order representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique order identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this order")
    customer_id: UUID = Field(description="Customer UUID who placed this order")
    status: OrderStatus = Field(description="Current order lifecycle status")
    total_amount: Decimal = Field(description="Authoritative total order amount as Decimal")
    currency: str = Field(description="Three-letter currency code")
    notes: Optional[str] = Field(default=None, description="Order notes")
    created_at: datetime = Field(description="Timestamp when order was placed")
    updated_at: datetime = Field(description="Timestamp when order was last updated")
    items: Optional[List[OrderItemResponse]] = Field(default=None, description="Optional nested line items")
