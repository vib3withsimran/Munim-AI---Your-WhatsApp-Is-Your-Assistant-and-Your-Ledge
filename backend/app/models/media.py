from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class MediaFile(BaseModel):
    """Domain model representing a row in the Supabase 'media_files' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique media identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this media")
    customer_id: Optional[UUID] = Field(default=None, description="Optional customer ID associated with this media")
    storage_bucket: str = Field(description="Supabase Storage bucket name")
    storage_path: str = Field(description="Relative storage path within the bucket")
    media_type: str = Field(description="High-level media type ('image', 'audio', 'document')")
    purpose: Optional[str] = Field(default=None, description="Business purpose ('upi_proof', 'voice_note', 'order_note', 'product_image', 'attachment')")
    processing_status: Optional[str] = Field(default="uploaded", description="Lifecycle status ('uploaded', 'processing', 'processed', 'failed')")
    created_at: datetime = Field(description="Timestamp when record was created")

