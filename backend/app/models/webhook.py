from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class WebhookProcessingStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    QUARANTINED = "quarantined"


class SellerWhatsAppChannel(BaseModel):
    """Domain model representing a seller's registered incoming WhatsApp receiving channel."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Channel mapping identifier")
    seller_id: UUID = Field(description="Tenant seller ID who owns this phone channel")
    phone_number: str = Field(description="Normalized phone number, e.g. '+14155238886'")
    display_name: Optional[str] = Field(default=None, description="Optional friendly label for channel")
    is_active: bool = Field(default=True, description="Whether channel is actively routing traffic")
    created_at: datetime = Field(description="Channel registration timestamp")
    updated_at: datetime = Field(description="Channel update timestamp")


class WebhookMessage(BaseModel):
    """Domain model representing an incoming webhook event log and idempotency barrier."""

    model_config = ConfigDict(from_attributes=True)

    message_sid: str = Field(description="Twilio unique MessageSid (Primary Key)")
    seller_id: Optional[UUID] = Field(default=None, description="Resolved tenant seller ID")
    from_phone: str = Field(description="Customer phone number")
    to_phone: str = Field(description="Receiving Twilio channel phone number")
    media_type: str = Field(default="text", description="Media type (text, image, audio, media)")
    raw_text: Optional[str] = Field(default=None, description="Incoming text body or caption")
    processing_status: str = Field(
        default=WebhookProcessingStatus.PROCESSING.value,
        description="Pipeline processing lifecycle status",
    )
    intent: Optional[str] = Field(default=None, description="Extracted intent (e.g. order, payment, inquiry)")
    error_message: Optional[str] = Field(default=None, description="Error reason if processing failed or quarantined")
    response_summary: Optional[str] = Field(default=None, description="Generated reply text sent to customer")
    created_at: datetime = Field(description="Webhook ingestion timestamp")
    processed_at: Optional[datetime] = Field(default=None, description="Processing completion timestamp")

