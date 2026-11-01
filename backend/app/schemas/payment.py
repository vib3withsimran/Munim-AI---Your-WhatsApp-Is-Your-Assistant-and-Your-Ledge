from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PaymentStatus(str, Enum):
    """Supported payment verification and lifecycle statuses."""

    PENDING = "pending"
    VERIFICATION_REQUIRED = "verification_required"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    COMPLETED = "completed"  # Backward compatibility with existing records


class PaymentMethod(str, Enum):
    """Supported payment modes / channels."""

    UPI = "upi"
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"


class PaymentCreateRequest(BaseModel):
    """
    Payload to record a payment.
    Supports linked payments (with order_id) or unlinked payments (order_id=None).
    AI extraction confidence is never accepted as payment verification.
    """

    model_config = ConfigDict(extra="forbid")

    order_id: Optional[UUID] = Field(
        default=None,
        description="Associated order ID (None for unlinked/advance payments)"
    )
    amount: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        description="Monetary amount received (non-negative Decimal)"
    )
    method: Optional[PaymentMethod] = Field(
        default=PaymentMethod.UPI,
        description="Payment method used (e.g. upi, cash, card)"
    )
    status: Optional[PaymentStatus] = Field(
        default=PaymentStatus.PENDING,
        description="Payment verification status (default: pending)"
    )
    transaction_reference: Optional[str] = Field(
        default=None,
        max_length=150,
        description="UTR, UPI reference ID or bank transaction reference"
    )
    paid_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when payment was executed by the customer"
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError("Payment amount cannot be negative")
        return round(v, 2)


class PaymentStatusUpdateRequest(BaseModel):
    """Payload to update verification status of an existing payment."""

    model_config = ConfigDict(extra="forbid")

    status: PaymentStatus = Field(description="Target payment status (e.g. verified, rejected)")


class PaymentLinkRequest(BaseModel):
    """Payload to link an unlinked payment to a specific order."""

    model_config = ConfigDict(extra="forbid")

    order_id: UUID = Field(description="Target order UUID to link this payment to")


class PaymentResponse(BaseModel):
    """Payment representation returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique payment record identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this payment record")
    order_id: Optional[UUID] = Field(default=None, description="Linked order UUID or None if unlinked")
    amount: Decimal = Field(description="Payment amount as Decimal")
    method: Optional[str] = Field(default=None, description="Payment method")
    status: PaymentStatus = Field(description="Payment status")
    transaction_reference: Optional[str] = Field(default=None, description="Transaction reference ID")
    paid_at: Optional[datetime] = Field(default=None, description="Execution timestamp")
    created_at: datetime = Field(description="Timestamp when record was inserted")
