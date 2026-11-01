from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Inventory(BaseModel):
    """Domain model representing a row in the Supabase 'inventory' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique inventory record identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this inventory record")
    variant_id: UUID = Field(description="Foreign key referencing product_variants.id")
    available_quantity: int = Field(default=0, ge=0, description="Available stock quantity for sale")
    reserved_quantity: int = Field(default=0, ge=0, description="Reserved stock held for active/pending orders")
    low_stock_threshold: int = Field(default=5, ge=0, description="Threshold below which low-stock alerts trigger")
    updated_at: datetime = Field(description="Timestamp when inventory was last updated")

