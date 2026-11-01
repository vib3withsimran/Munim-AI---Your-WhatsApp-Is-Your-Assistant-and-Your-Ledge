from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MediaResponse(BaseModel):
    """Schema returned for media file queries and uploads."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique media identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this media")
    customer_id: Optional[UUID] = Field(default=None, description="Customer ID associated with media")
    storage_bucket: str = Field(description="Storage bucket name")
    storage_path: str = Field(description="Relative storage path")
    media_type: str = Field(description="Media type (image, audio, document)")
    purpose: Optional[str] = Field(default=None, description="Business category/purpose")
    processing_status: Optional[str] = Field(default="uploaded", description="Processing status")
    created_at: datetime = Field(description="Creation timestamp")
    signed_url: Optional[str] = Field(default=None, description="Short-lived signed download URL")


class MediaUrlResponse(BaseModel):
    """Schema returned for short-lived signed URL requests."""

    signed_url: str = Field(description="Short-lived signed download URL")
    expires_in: int = Field(description="Validity duration in seconds")

