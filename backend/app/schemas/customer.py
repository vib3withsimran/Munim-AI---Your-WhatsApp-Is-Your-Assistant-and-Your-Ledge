import re
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_REGEX = re.compile(r"^\+?[0-9]{10,15}$")


def validate_phone_number(val: str) -> str:
    """
    Validates and normalizes phone numbers to standard format.
    Accepts 10-15 digits with optional leading '+'.
    Strips internal spaces, hyphens, and parentheses.
    """
    if not val or not isinstance(val, str):
        raise ValueError("Phone number must be a non-empty string")
    cleaned = re.sub(r"[\s\-\(\)\.]", "", val.strip())
    if not PHONE_REGEX.match(cleaned):
        raise ValueError("Phone number must contain between 10 and 15 digits with optional leading '+'")
    return cleaned


class CustomerCreateRequest(BaseModel):
    """Payload to create a new customer. Seller ownership is derived from JWT context."""

    model_config = ConfigDict(extra="forbid")

    phone: str = Field(description="Customer phone number (10-15 digits with optional leading '+')")
    name: Optional[str] = Field(default=None, max_length=150, description="Customer name if known")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Optional merchant notes")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_phone_number(v)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None


class CustomerUpdateRequest(BaseModel):
    """Payload to update an existing customer."""

    model_config = ConfigDict(extra="forbid")

    phone: Optional[str] = Field(default=None, description="Updated phone number")
    name: Optional[str] = Field(default=None, max_length=150, description="Updated name")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Updated merchant notes")

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_phone_number(v)
        return None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None


class CustomerResponse(BaseModel):
    """Customer representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique customer identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this customer")
    phone: str = Field(description="Customer phone number")
    name: Optional[str] = Field(default=None, description="Customer name")
    notes: Optional[str] = Field(default=None, description="Merchant notes")
    created_at: datetime = Field(description="Timestamp when customer was created")
