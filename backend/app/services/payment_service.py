import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.payment import Payment
from backend.app.models.order import Order
from backend.app.schemas.payment import (
    PaymentCreateRequest,
    PaymentStatus,
)
from backend.app.repositories.payment_repository import PaymentRepository
from backend.app.repositories.order_repository import OrderRepository
from backend.app.repositories.exceptions import NotFoundError, ConstraintViolationError, ForeignKeyViolationError
from backend.app.services.exceptions import (
    BusinessRuleError,
    InvalidPaymentTransitionError,
    AmbiguousPaymentMatchError,
)

logger = logging.getLogger(__name__)

# Allowed payment status transitions
VALID_PAYMENT_TRANSITIONS: Dict[str, List[str]] = {
    "pending": ["verification_required", "verified", "rejected"],
    "verification_required": ["verified", "rejected"],
    "verified": ["refunded"],
    "rejected": [],   # Terminal
    "refunded": [],   # Terminal
    "completed": ["refunded"],  # Terminal / refund
}

VERIFIED_STATUSES = {"verified", "completed"}


class PaymentService:
    """
    Business logic service for payment recording, status lifecycle,
    reconciliation, and order matching.
    """

    def __init__(self, db: Client):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.order_repo = OrderRepository(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_payment(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID]
    ) -> Optional[Payment]:
        """Fetches payment by ID with strict seller ownership verification."""
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(payment_id)
        return self.payment_repo.get_payment_by_id(seller_id=sid, payment_id=pid)

    def list_payments(
        self,
        seller_id: Union[str, UUID],
        status: Optional[str] = None,
        order_id: Optional[Union[str, UUID]] = None,
        unlinked_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Payment]:
        """Lists payments owned by seller with optional status, order filters, and unlinked filter."""
        sid = self._normalize_id(seller_id)
        return self.payment_repo.list_payments(
            seller_id=sid,
            status=status,
            order_id=order_id,
            unlinked_only=unlinked_only,
            limit=limit,
            offset=offset
        )

    def get_order_payments(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> List[Payment]:
        """Retrieves all payments associated with an order."""
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)
        return self.payment_repo.get_payments_by_order(seller_id=sid, order_id=oid)

    # =========================================================================
    # Balance & Dues Calculation (Supports Partial Payments)
    # =========================================================================

    def calculate_order_paid_amount(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> Decimal:
        """
        Calculates total verified amount paid towards an order.
        Only payments with status 'verified' or 'completed' are credited.
        Unverified, pending, or rejected payments do NOT reduce outstanding dues.
        """
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)
        payments = self.get_order_payments(seller_id=sid, order_id=oid)

        paid_total = Decimal("0.00")
        for p in payments:
            if str(p.status).lower() in VERIFIED_STATUSES:
                paid_total += Decimal(str(p.amount))
        return round(paid_total, 2)

    def calculate_outstanding_balance(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> Decimal:
        """
        Calculates remaining balance due on an order.
        outstanding = max(0.00, order.total_amount - verified_paid_amount)
        """
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        order = self.order_repo.get_order_by_id(seller_id=sid, order_id=oid)
        if not order:
            raise NotFoundError(f"Order '{oid}' not found.")

        paid = self.calculate_order_paid_amount(seller_id=sid, order_id=oid)
        order_total = Decimal(str(order.total_amount))
        outstanding = order_total - paid
        return max(Decimal("0.00"), round(outstanding, 2))

    # =========================================================================
    # Payment Matching Engine
    # =========================================================================

    def find_matching_order(
        self,
        seller_id: Union[str, UUID],
        customer_id: Optional[Union[str, UUID]] = None,
        amount: Optional[Decimal] = None,
        transaction_reference: Optional[str] = None
    ) -> Optional[Order]:
        """
        Matching Rules:
        1. Match using exact unique UPI transaction reference across existing payments (if linked).
        2. Otherwise match exact outstanding balance when exactly ONE eligible order exists for customer.
        3. If multiple orders match amount, raise AmbiguousPaymentMatchError to escalate.
        4. If zero orders match, return None (unlinked payment for owner review).
        """
        sid = self._normalize_id(seller_id)

        # Rule 1: Check if this transaction reference was previously matched
        if transaction_reference and transaction_reference.strip():
            clean_ref = transaction_reference.strip()
            existing_pay = self.payment_repo.find_payment_by_transaction_reference(seller_id=sid, reference=clean_ref)
            if existing_pay and existing_pay.order_id:
                return self.order_repo.get_order_by_id(seller_id=sid, order_id=existing_pay.order_id)

        # Require customer_id and amount for order balance matching
        if not customer_id or amount is None:
            return None

        cid = self._normalize_id(customer_id)
        target_amount = round(Decimal(str(amount)), 2)

        # Fetch active non-cancelled orders for customer
        customer_orders = self.order_repo.get_orders_by_customer(seller_id=sid, customer_id=cid, limit=50)
        active_orders = [o for o in customer_orders if str(o.status).lower() not in ("cancelled", "canceled")]

        matching_orders: List[Order] = []
        for ord_obj in active_orders:
            due = self.calculate_outstanding_balance(seller_id=sid, order_id=ord_obj.id)
            if due == target_amount:
                matching_orders.append(ord_obj)

        if len(matching_orders) == 1:
            return matching_orders[0]
        elif len(matching_orders) > 1:
            raise AmbiguousPaymentMatchError(
                f"Payment amount ₹{target_amount} matches {len(matching_orders)} orders for customer '{cid}'. Escalate for manual merchant review."
            )

        return None

    # =========================================================================
    # Lifecycle & Verification Transitions
    # =========================================================================

    @staticmethod
    def validate_payment_status_transition(current_status: str, target_status: str) -> bool:
        """
        Validates whether target_status is a valid progression from current_status.
        Never allows AI extraction confidence to verify a payment.
        """
        curr = current_status.lower().strip()
        tgt = target_status.lower().strip()

        if curr == tgt:
            return True  # Idempotent

        allowed_targets = VALID_PAYMENT_TRANSITIONS.get(curr, [])
        if tgt not in allowed_targets:
            raise InvalidPaymentTransitionError(from_status=curr, to_status=tgt)
        return True

    def record_payment(
        self,
        seller_id: Union[str, UUID],
        data: PaymentCreateRequest,
        is_owner_action: bool = False
    ) -> Payment:
        """
        Records a payment.
        Enforces schema constraint (order_id required until migration).
        Security Rule: Cannot set status to 'verified' from untrusted extraction.
        Requires explicit merchant action (is_owner_action=True) or webhook verification signature.
        """
        sid = self._normalize_id(seller_id)

        # Prevent untrusted auto-verification
        if data.status in (PaymentStatus.VERIFIED, PaymentStatus.COMPLETED) and not is_owner_action:
            logger.warning("Attempted to record auto-verified payment without owner approval; forcing status=pending")
            data = data.model_copy(update={"status": PaymentStatus.PENDING})

        return self.payment_repo.create_payment(seller_id=sid, data=data)

    def update_payment_status(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID],
        new_status: Union[str, PaymentStatus],
        is_owner_action: bool = False
    ) -> Payment:
        """
        Transitions payment status.
        Verifying a payment requires explicit merchant authorization (is_owner_action=True).
        """
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(payment_id)
        target = new_status.value if isinstance(new_status, PaymentStatus) else str(new_status)

        payment = self.get_payment(seller_id=sid, payment_id=pid)
        if not payment:
            raise NotFoundError(f"Payment '{pid}' not found or not owned by this seller.")

        # Enforce transition rules
        self.validate_payment_status_transition(current_status=payment.status, target_status=target)

        if target in ("verified", "completed") and not is_owner_action:
            raise ConstraintViolationError("Payment verification requires explicit business owner approval.")

        update_dict = {
            "status": target,
        }
        if target in ("verified", "completed") and not payment.paid_at:
            update_dict["paid_at"] = datetime.now(timezone.utc).isoformat()

        try:
            res = (
                self.db.table("payments")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("id", pid)
                .execute()
            )
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            return Payment.model_validate(row)
        except Exception as e:
            if isinstance(e, (InvalidPaymentTransitionError, ConstraintViolationError)):
                raise
            raise RuntimeError(f"Failed to update payment status: {e}")

    def verify_payment(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID]
    ) -> Payment:
        """Verifies a pending payment as authenticated merchant."""
        return self.update_payment_status(
            seller_id=seller_id,
            payment_id=payment_id,
            new_status=PaymentStatus.VERIFIED,
            is_owner_action=True,
        )

    def reject_payment(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID]
    ) -> Payment:
        """Rejects a payment as authenticated merchant."""
        return self.update_payment_status(
            seller_id=seller_id,
            payment_id=payment_id,
            new_status=PaymentStatus.REJECTED,
            is_owner_action=True,
        )

    def link_payment_to_order(
        self,
        seller_id: Union[str, UUID],
        payment_id: Union[str, UUID],
        order_id: Union[str, UUID],
        is_owner_action: bool = True
    ) -> Payment:
        """
        Links an unlinked payment to an eligible order after merchant review.
        - Rejects linking to cross-seller orders (NotFoundError).
        - Rejects linking to non-existent orders.
        - Rejects linking to cancelled orders.
        - Rejects linking a payment that is already linked to another order.
        """
        sid = self._normalize_id(seller_id)
        pid = self._normalize_id(payment_id)
        oid = self._normalize_id(order_id)

        payment = self.get_payment(seller_id=sid, payment_id=pid)
        if not payment:
            raise NotFoundError(f"Payment '{pid}' not found or not owned by this seller.")

        if payment.order_id and str(payment.order_id) != oid:
            raise BusinessRuleError(f"Payment '{pid}' is already linked to order '{payment.order_id}'.")

        order = self.order_repo.get_order_by_id(seller_id=sid, order_id=oid)
        if not order:
            raise NotFoundError(f"Order '{oid}' not found or not owned by this seller.")

        if str(order.status).lower() in ("cancelled", "canceled"):
            raise BusinessRuleError(f"Cannot link payment to cancelled order '{oid}'.")

        return self.payment_repo.link_payment_to_order(seller_id=sid, payment_id=pid, order_id=oid)

