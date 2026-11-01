from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryUpdateRequest(BaseModel):
    """Payload to update inventory stock levels and thresholds for a variant."""

    model_config = ConfigDict(extra="forbid")

    available_quantity: Optional[int] = Field(default=None, ge=0, description="Available stock quantity (non-negative integer)")
    reserved_quantity: Optional[int] = Field(default=None, ge=0, description="Reserved stock quantity (non-negative integer)")
    low_stock_threshold: Optional[int] = Field(default=None, ge=0, description="Low stock threshold (non-negative integer)")

    @field_validator("available_quantity", "reserved_quantity", "low_stock_threshold")
    @classmethod
    def check_non_negative(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Quantity and threshold values cannot be negative")
        return v


class InventoryResponse(BaseModel):
    """Inventory representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique inventory record identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this inventory record")
    variant_id: UUID = Field(description="Associated product variant UUID")
    available_quantity: int = Field(description="Stock available for purchase")
    reserved_quantity: int = Field(description="Stock reserved for unfulfilled orders")
    low_stock_threshold: int = Field(description="Threshold for low-stock warnings")
    updated_at: datetime = Field(description="Timestamp when inventory was last updated")
