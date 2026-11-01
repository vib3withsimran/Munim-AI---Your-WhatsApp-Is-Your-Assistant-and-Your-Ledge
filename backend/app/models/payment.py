from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Payment(BaseModel):
    """Domain model representing a row in the Supabase 'payments' table."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="Unique payment record identifier (UUID)")
    seller_id: UUID = Field(description="Tenant seller ID owning this payment")
    order_id: Optional[UUID] = Field(default=None, description="Optional foreign key referencing orders.id (None for unlinked/advance payments)")
    amount: Decimal = Field(description="Payment amount as Decimal", ge=Decimal("0.00"))
    method: Optional[str] = Field(default=None, description="Payment method (e.g. upi, cash, card, bank_transfer)")
    status: str = Field(description="Payment verification status (e.g. pending, verified, rejected, completed)")
    transaction_reference: Optional[str] = Field(default=None, description="Bank / UPI reference or transaction ID")
    paid_at: Optional[datetime] = Field(default=None, description="Timestamp when payment was executed")
    created_at: datetime = Field(description="Timestamp when record was created in database")

