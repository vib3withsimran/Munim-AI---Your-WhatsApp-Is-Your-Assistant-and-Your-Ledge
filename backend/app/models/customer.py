from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Customer(BaseModel):
    """Domain model representing a row in the Supabase 'customers' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique customer identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this customer")
    phone: str = Field(description="Customer phone number (normalized format)")
    name: Optional[str] = Field(default=None, description="Customer name if known")
    notes: Optional[str] = Field(default=None, description="Optional merchant notes about customer")
    created_at: datetime = Field(description="Timestamp when customer was created")

