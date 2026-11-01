import logging
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.payment import Payment
from backend.app.schemas.payment import PaymentCreateRequest, PaymentStatus
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    ForeignKeyViolationError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class PaymentRepository:
    """Data-access repository for the Supabase 'payments' table."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def create_payment(
        self,
        seller_id: Union[str, UUID],
        data: PaymentCreateRequest
    ) -> Payment:
        """
        Creates a payment record owned by seller_id.
        Enforces schema constraint: order_id cannot be None until database migration is applied.
        Ensures referenced order belongs to the seller.
        Never automatically verifies payments.
        """
        sid = self._normalize_id(seller_id)

        # Enforce live schema constraint: order_id is required
        if data.order_id is None:
            raise ConstraintViolationError(
                "Cannot insert unlinked payment: live database schema requires 'order_id' (NOT NULL). "
                "A migration is required before unlinked payments can be stored."
            )

        oid = self._normalize_id(data.order_id)

        # Verify referenced order belongs to the same seller
        order_check = (
            self.db.table("orders")
            .select("id")
            .eq("seller_id", sid)
            .eq("id", oid)
            .maybe_single()
            .execute()
        )
        check_row = order_check.data[0] if isinstance(order_check.data, list) and order_check.data else order_check.data
        if not check_row:
            raise ForeignKeyViolationError(
                f"Referenced order '{oid}' does not exist or does not belong to this seller."
            )

        # Ensure payment status does not automatically bypass verification
        status_val = data.status.value if isinstance(data.status, PaymentStatus) else str(data.status or "pending")

        payload = {
            "seller_id": sid,
            "order_id": oid,
            "amount": float(data.amount),
            "method": data.method.value if hasattr(data.method, "value") else str(data.method or "upi"),
            "status": status_val,
            "transaction_reference": data.transaction_reference,
            "paid_at": data.paid_at.isoformat() if data.paid_at else None,
        }

        try:
            res = (
                self.db.table("payments")
                .insert(payload)
                .execute()
            )
            if not res.data:
                raise RuntimeError("Failed to insert payment record")
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Payment.model_validate(row)
        except Exception as e:
            if isinstance(e, (ConstraintViolationError, ForeignKeyViolationError)):
                raise
            raise map_supabase_error(e, entity="Payment")

    def get_payment_by_id(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID]
    ) -> Optional[Payment]:
        """Fetches a single payment by ID, strictly scoped to seller_id."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(payment_id)

        try:
            res = (
                self.db.table("payments")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", pid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Payment.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Payment")

    def list_payments(
        self,
        seller_id: Union[str, UUID],
        status: Optional[str] = None,
        order_id: Optional[Union[str, UUID]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Payment]:
        """Lists payments owned by seller with optional status and order filters and pagination."""
        sid = self._normalize_id(seller_id)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            query = (
                self.db.table("payments")
                .select("*")
                .eq("seller_id", sid)
            )

            if status is not None:
                query = query.eq("status", status.lower().strip())
            if order_id is not None:
                query = query.eq("order_id", self._normalize_id(order_id))

            res = (
                query
                .order("created_at", desc=True)
                .range(safe_offset, safe_offset + safe_limit - 1)
                .execute()
            )
            rows = res.data or []
            return [Payment.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="Payment")

    def get_payments_by_order(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> List[Payment]:
        """Convenience method to retrieve all payments associated with an order."""
        return self.list_payments(
            seller_id=seller_id,
            order_id=order_id,
            limit=100
        )

    def find_payment_by_transaction_reference(
        self,
        seller_id: Union[str, UUID],
        reference: str
    ) -> Optional[Payment]:
        """Finds a payment by UTR or transaction reference string for this seller."""
        sid = self._normalize_id(seller_id)
        clean_ref = reference.strip()

        try:
            res = (
                self.db.table("payments")
                .select("*")
                .eq("seller_id", sid)
                .eq("transaction_reference", clean_ref)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Payment.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Payment")
