from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PrivacySetting(BaseModel):
    """Domain model representing customer privacy toggle per seller."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = Field(default=None, description="Primary key UUID")
    seller_id: UUID = Field(description="Seller UUID")
    customer_id: UUID = Field(description="Customer UUID")
    is_private: bool = Field(default=False, description="Whether privacy mode is enabled")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

