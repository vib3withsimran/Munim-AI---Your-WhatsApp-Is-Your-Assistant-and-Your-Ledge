import re
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


def normalize_whatsapp_phone(phone: str) -> str:
    """
    Normalizes incoming WhatsApp phone number to standard E.164 format:
    - Removes 'whatsapp:' URI prefix.
    - Strips whitespace, dashes, parens.
    - Ensures standard '+' prefix if digits-only international number.
    """
    cleaned = (phone or "").replace("whatsapp:", "").strip()
    cleaned = re.sub(r"[\s\-\(\)]", "", cleaned)
    if cleaned and not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"
    return cleaned


class ChannelCreateRequest(BaseModel):
    """Schema for registering a WhatsApp phone number channel for a seller."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., description="E.164 phone number, e.g. +14155238886")
    display_name: Optional[str] = Field(default=None, max_length=100, description="Display label")
    is_active: bool = Field(default=True, description="Active status")


class ChannelResponse(BaseModel):
    """Schema for returning registered WhatsApp channel info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    phone_number: str
    display_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WebhookMessageResponse(BaseModel):
    """Schema for webhook message status lookup."""

    model_config = ConfigDict(from_attributes=True)

    message_sid: str
    seller_id: Optional[UUID] = None
    from_phone: str
    to_phone: str
    media_type: str
    raw_text: Optional[str] = None
    processing_status: str
    intent: Optional[str] = None
    error_message: Optional[str] = None
    response_summary: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


class IncomingTwilioPayload(BaseModel):
    """Normalized payload parsed from Twilio form data."""

    model_config = ConfigDict(extra="ignore")

    message_sid: str = Field(..., description="Twilio MessageSid")
    from_phone: str = Field(..., description="Normalized From number")
    to_phone: str = Field(..., description="Normalized To number")
    profile_name: Optional[str] = Field(default=None, description="Sender WhatsApp profile name")
    body: Optional[str] = Field(default=None, description="Message text body")
    num_media: int = Field(default=0, description="Number of media attachments")
    media_url: Optional[str] = Field(default=None, description="URL of primary media file")
    media_content_type: Optional[str] = Field(default=None, description="Content-Type of primary media")

