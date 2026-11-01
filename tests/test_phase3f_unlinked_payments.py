import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
import pytest

from fastapi import status
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.payment import (
    PaymentCreateRequest,
    PaymentLinkRequest,
    PaymentStatus,
    PaymentMethod,
)
from backend.app.services.payment_service import PaymentService
from backend.app.services.exceptions import (
    BusinessRuleError,
    AmbiguousPaymentMatchError,
    InvalidPaymentTransitionError,
)
from backend.app.repositories.exceptions import (
    NotFoundError,
    ForeignKeyViolationError,
    DuplicateRecordError,
)

client = TestClient(app)


# ============================================================================
# Helpers & Model Factories
# ============================================================================

SELLER_A_ID = "11111111-1111-1111-1111-111111111111"
SELLER_B_ID = "22222222-2222-2222-2222-222222222222"


def make_order_dict(
    oid: str,
    seller_id: str = SELLER_A_ID,
    total_amount: Any = "1000.00",
    order_status: str = "pending",
    customer_id: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "id": oid,
        "seller_id": seller_id,
        "customer_id": customer_id or str(uuid.uuid4()),
        "status": order_status,
        "total_amount": Decimal(str(total_amount)),
        "currency": "INR",
        "notes": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def make_payment_dict(
    pid: str,
    seller_id: str = SELLER_A_ID,
    order_id: Optional[str] = None,
    amount: Any = "500.00",
    pay_status: str = "pending",
    ref: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "id": pid,
        "seller_id": seller_id,
        "order_id": order_id,
        "amount": Decimal(str(amount)),
        "method": "upi",
        "status": pay_status,
        "transaction_reference": ref,
        "paid_at": datetime.now(timezone.utc).isoformat() if pay_status == "verified" else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ============================================================================
# Mock Storage & PostgREST Engine
# ============================================================================

class MockQuery:
    def __init__(self, table_name: str, store: dict):
        self.table_name = table_name
        self.store = store
        self.rows = list(self.store.get(table_name, []))
        self._action = "select"
        self._payload = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, column: str, value: Any):
        self.rows = [r for r in self.rows if str(r.get(column)) == str(value)]
        return self

    def is_(self, column: str, value: Any):
        if str(value).lower() in ("null", "none"):
            self.rows = [r for r in self.rows if r.get(column) is None]
        else:
            self.rows = [r for r in self.rows if r.get(column) == value]
        return self

    def in_(self, column: str, values: list):
        str_vals = [str(v) for v in values]
        self.rows = [r for r in self.rows if str(r.get(column)) in str_vals]
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def range(self, start: int, end: int):
        self.rows = self.rows[start:end + 1]
        return self

    def maybe_single(self):
        res = MagicMock()
        res.data = self.rows[0] if self.rows else None
        return self

    def single(self):
        return self.maybe_single()

    def insert(self, payload: dict):
        self._action = "insert"
        new_row = dict(payload)
        if "id" not in new_row:
            new_row["id"] = str(uuid.uuid4())
        if "created_at" not in new_row:
            new_row["created_at"] = datetime.now(timezone.utc).isoformat()
        if "updated_at" not in new_row and self.table_name in ("products", "orders", "inventory"):
            new_row["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._payload = new_row
        return self

    def update(self, payload: dict):
        self._action = "update"
        self._payload = payload
        return self

    def execute(self):
        res = MagicMock()
        if self._action == "insert":
            self.store[self.table_name].append(self._payload)
            res.data = [self._payload]
            return res
        elif self._action == "update":
            updated_rows = []
            for r in self.rows:
                r.update(self._payload)
                updated_rows.append(r)
            res.data = updated_rows
            return res
        else:
            res.data = self.rows
            return res


class MockDatabase:
    def __init__(self, initial_data: dict = None, authenticated_uid: str = None):
        self.store = initial_data or {
            "customers": [],
            "orders": [],
            "order_items": [],
            "payments": [],
        }
        self.authenticated_uid = authenticated_uid
        self.postgrest = MagicMock()
        self.auth = MagicMock()

    def table(self, name: str):
        if name not in self.store:
            self.store[name] = []
        return MockQuery(name, self.store)


@pytest.fixture
def mock_db():
    return MockDatabase(authenticated_uid=SELLER_A_ID)


@pytest.fixture
def auth_seller_a(mock_db):
    seller = AuthenticatedSeller(id=SELLER_A_ID, db=mock_db)
    app.dependency_overrides[get_current_seller] = lambda: seller
    yield seller
    app.dependency_overrides.pop(get_current_seller, None)


# ============================================================================
# 1. Unlinked Payment Creation Tests
# ============================================================================

class TestUnlinkedPaymentCreation:
    def test_create_linked_payment_success(self, auth_seller_a, mock_db):
        """Creating payment with valid order_id succeeds."""
        oid = str(uuid.uuid4())
        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1000.00"))

        payload = {
            "order_id": oid,
            "amount": 500.0,
            "method": "upi",
            "transaction_reference": "UTR-LINKED-001",
        }
        res = client.post("/api/payments", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["order_id"] == oid
        assert Decimal(str(data["amount"])) == Decimal("500.00")
        assert data["status"] == "pending"

    def test_create_unlinked_payment_with_explicit_none(self, auth_seller_a):
        """Creating payment with order_id=None succeeds (Phase 3F unlinked payment)."""
        payload = {
            "order_id": None,
            "amount": 750.50,
            "method": "upi",
            "transaction_reference": "UTR-UNLINKED-001",
        }
        res = client.post("/api/payments", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["order_id"] is None
        assert Decimal(str(data["amount"])) == Decimal("750.50")
        assert data["seller_id"] == SELLER_A_ID

    def test_create_unlinked_payment_with_omitted_order_id(self, auth_seller_a):
        """Creating payment without order_id field succeeds as unlinked."""
        payload = {
            "amount": 1200.00,
            "method": "cash",
        }
        res = client.post("/api/payments", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["order_id"] is None
        assert Decimal(str(data["amount"])) == Decimal("1200.00")

    def test_unlinked_payment_rejects_negative_amount(self, auth_seller_a):
        """Negative payment amounts are strictly rejected by schema validation."""
        payload = {
            "order_id": None,
            "amount": -50.0,
        }
        res = client.post("/api/payments", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unlinked_payment_untrusted_verification_attempt_forced_pending(self, mock_db):
        """AI extraction or untrusted client cannot auto-verify payment."""
        service = PaymentService(mock_db)
        req = PaymentCreateRequest(
            order_id=None,
            amount=Decimal("500.00"),
            status=PaymentStatus.VERIFIED,  # Untrusted attempt
        )
        pay = service.record_payment(seller_id=SELLER_A_ID, data=req, is_owner_action=False)
        assert pay.status == "pending"


# ============================================================================
# 2. Payment Retrieval & Listing Tests
# ============================================================================

class TestPaymentRetrievalAndListing:
    def test_list_payments_includes_both_linked_and_unlinked(self, auth_seller_a, mock_db):
        """GET /api/payments retrieves all payments owned by seller."""
        mock_db.store["payments"].extend([
            make_payment_dict(str(uuid.uuid4()), order_id=str(uuid.uuid4()), amount="100.00"),
            make_payment_dict(str(uuid.uuid4()), order_id=None, amount="200.00"),
        ])

        res = client.get("/api/payments", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 2

    def test_list_payments_filter_unlinked_only(self, auth_seller_a, mock_db):
        """GET /api/payments?unlinked_only=true retrieves ONLY unlinked payments."""
        linked_id = str(uuid.uuid4())
        unlinked_id = str(uuid.uuid4())
        mock_db.store["payments"].extend([
            make_payment_dict(linked_id, order_id=str(uuid.uuid4()), amount="100.00"),
            make_payment_dict(unlinked_id, order_id=None, amount="200.00"),
        ])

        res = client.get("/api/payments?unlinked_only=true", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 1
        assert data[0]["id"] == unlinked_id
        assert data[0]["order_id"] is None

    def test_get_unlinked_payment_by_id(self, auth_seller_a, mock_db):
        """GET /api/payments/{id} retrieves unlinked payment."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="450.00"))

        res = client.get(f"/api/payments/{pid}", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["order_id"] is None
        assert Decimal(str(res.json()["amount"])) == Decimal("450.00")


# ============================================================================
# 3. Payment Linking Tests
# ============================================================================

class TestPaymentLinking:
    def test_link_unlinked_payment_to_order_success(self, auth_seller_a, mock_db):
        """Owner links an unlinked payment to a valid order."""
        oid = str(uuid.uuid4())
        pid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1500.00"))
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="1500.00"))

        # Link
        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": oid},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["order_id"] == oid

        # Verify in database
        pay = next(p for p in mock_db.store["payments"] if p["id"] == pid)
        assert pay["order_id"] == oid

    def test_link_payment_rejects_cross_seller_order(self, auth_seller_a, mock_db):
        """Attempting to link a payment to an order owned by Seller B returns 404."""
        seller_b_order = str(uuid.uuid4())
        pid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=seller_b_order, seller_id=SELLER_B_ID, total_amount="800.00"))
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="800.00"))

        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": seller_b_order},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_link_payment_rejects_nonexistent_order(self, auth_seller_a, mock_db):
        """Linking to random nonexistent order returns 404."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="500.00"))

        nonexistent_oid = str(uuid.uuid4())
        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": nonexistent_oid},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_link_payment_rejects_cancelled_order(self, auth_seller_a, mock_db):
        """Cannot link payments to a cancelled order (400 BusinessRuleError)."""
        oid = str(uuid.uuid4())
        pid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1000.00", order_status="cancelled"))
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="1000.00"))

        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": oid},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "cancelled" in res.json()["detail"].lower()

    def test_link_already_linked_payment_to_different_order_rejected(self, auth_seller_a, mock_db):
        """Cannot relink a payment already linked to Order 1 to Order 2."""
        ord_1 = str(uuid.uuid4())
        ord_2 = str(uuid.uuid4())
        pid = str(uuid.uuid4())

        mock_db.store["orders"].extend([
            make_order_dict(oid=ord_1, total_amount="500.00"),
            make_order_dict(oid=ord_2, total_amount="500.00"),
        ])
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=ord_1, amount="500.00"))

        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": ord_2},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "already linked" in res.json()["detail"].lower()


# ============================================================================
# 4. Payment Matching & Ambiguity Tests
# ============================================================================

class TestPaymentMatchingAndAmbiguity:
    def test_matching_exact_single_order(self, mock_db):
        """Matching engine resolves single order with matching outstanding due."""
        service = PaymentService(mock_db)
        cid = str(uuid.uuid4())
        oid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1200.00", customer_id=cid))

        match = service.find_matching_order(
            seller_id=SELLER_A_ID,
            customer_id=cid,
            amount=Decimal("1200.00"),
        )
        assert match is not None
        assert str(match.id) == oid

    def test_matching_ambiguous_orders_raises_error(self, mock_db):
        """Multiple orders with identical due balance raises AmbiguousPaymentMatchError."""
        service = PaymentService(mock_db)
        cid = str(uuid.uuid4())
        oid_1 = str(uuid.uuid4())
        oid_2 = str(uuid.uuid4())

        mock_db.store["orders"].extend([
            make_order_dict(oid=oid_1, total_amount="850.00", customer_id=cid),
            make_order_dict(oid=oid_2, total_amount="850.00", customer_id=cid),
        ])

        with pytest.raises(AmbiguousPaymentMatchError) as exc_info:
            service.find_matching_order(
                seller_id=SELLER_A_ID,
                customer_id=cid,
                amount=Decimal("850.00"),
            )
        assert "matches 2 orders" in str(exc_info.value)

    def test_matching_zero_orders_returns_none(self, mock_db):
        """When no order matches amount, returns None (payment stays unlinked)."""
        service = PaymentService(mock_db)
        cid = str(uuid.uuid4())
        oid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1000.00", customer_id=cid))

        match = service.find_matching_order(
            seller_id=SELLER_A_ID,
            customer_id=cid,
            amount=Decimal("350.00"),  # Doesn't match 1000
        )
        assert match is None


# ============================================================================
# 5. Duplicate Transaction Reference Tests
# ============================================================================

class TestDuplicateTransactionReference:
    def test_duplicate_transaction_reference_rejected(self, auth_seller_a):
        """Second payment with identical transaction_reference for same seller returns 409."""
        payload1 = {
            "amount": 500.0,
            "transaction_reference": "UTR-DUP-12345",
        }
        res1 = client.post("/api/payments", json=payload1, headers={"Authorization": "Bearer dummy"})
        assert res1.status_code == status.HTTP_201_CREATED

        # Duplicate
        payload2 = {
            "amount": 300.0,
            "transaction_reference": "UTR-DUP-12345",
        }
        res2 = client.post("/api/payments", json=payload2, headers={"Authorization": "Bearer dummy"})
        assert res2.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in res2.json()["detail"].lower()

    def test_duplicate_transaction_reference_allowed_across_different_sellers(self, mock_db):
        """Different sellers can use the same transaction reference without collision."""
        service = PaymentService(mock_db)

        req_a = PaymentCreateRequest(amount=Decimal("500.00"), transaction_reference="UTR-SHARED-999")
        pay_a = service.record_payment(seller_id=SELLER_A_ID, data=req_a)
        assert pay_a.seller_id == uuid.UUID(SELLER_A_ID)

        req_b = PaymentCreateRequest(amount=Decimal("500.00"), transaction_reference="UTR-SHARED-999")
        pay_b = service.record_payment(seller_id=SELLER_B_ID, data=req_b)
        assert pay_b.seller_id == uuid.UUID(SELLER_B_ID)

    def test_multiple_payments_without_reference_allowed(self, auth_seller_a):
        """Multiple payments with None reference (e.g. cash) do not collide."""
        res1 = client.post("/api/payments", json={"amount": 100.0, "method": "cash"}, headers={"Authorization": "Bearer dummy"})
        assert res1.status_code == status.HTTP_201_CREATED

        res2 = client.post("/api/payments", json={"amount": 200.0, "method": "cash"}, headers={"Authorization": "Bearer dummy"})
        assert res2.status_code == status.HTTP_201_CREATED


# ============================================================================
# 6. Outstanding Balance Calculations Tests
# ============================================================================

class TestOutstandingBalanceCalculations:
    def test_unlinked_payment_does_not_reduce_order_dues(self, mock_db):
        """Unlinked payment (order_id=None) NEVER reduces an order's outstanding balance."""
        service = PaymentService(mock_db)
        oid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="2000.00"))
        # Unlinked verified payment exists
        mock_db.store["payments"].append(make_payment_dict(str(uuid.uuid4()), order_id=None, amount="2000.00", pay_status="verified"))

        paid = service.calculate_order_paid_amount(seller_id=SELLER_A_ID, order_id=oid)
        assert paid == Decimal("0.00")

        due = service.calculate_outstanding_balance(seller_id=SELLER_A_ID, order_id=oid)
        assert due == Decimal("2000.00")

    def test_linked_unverified_payment_does_not_reduce_order_dues(self, mock_db):
        """Unverified payment linked to an order does NOT reduce outstanding balance."""
        service = PaymentService(mock_db)
        oid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1500.00"))
        mock_db.store["payments"].append(make_payment_dict(str(uuid.uuid4()), order_id=oid, amount="1500.00", pay_status="pending"))

        paid = service.calculate_order_paid_amount(seller_id=SELLER_A_ID, order_id=oid)
        assert paid == Decimal("0.00")
        assert service.calculate_outstanding_balance(seller_id=SELLER_A_ID, order_id=oid) == Decimal("1500.00")

    def test_linked_verified_payment_reduces_order_dues(self, mock_db):
        """Once linked AND verified, payment reduces outstanding balance."""
        service = PaymentService(mock_db)
        oid = str(uuid.uuid4())

        mock_db.store["orders"].append(make_order_dict(oid=oid, total_amount="1500.00"))
        mock_db.store["payments"].append(make_payment_dict(str(uuid.uuid4()), order_id=oid, amount="1000.00", pay_status="verified"))

        paid = service.calculate_order_paid_amount(seller_id=SELLER_A_ID, order_id=oid)
        assert paid == Decimal("1000.00")
        assert service.calculate_outstanding_balance(seller_id=SELLER_A_ID, order_id=oid) == Decimal("500.00")


# ============================================================================
# 7. Verification & Rejection Permissions Tests
# ============================================================================

class TestVerificationAndRejectionPermissions:
    def test_unlinked_payment_can_be_verified_by_owner(self, auth_seller_a, mock_db):
        """Owner can verify an unlinked payment."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="700.00", pay_status="pending"))

        res = client.post(f"/api/payments/{pid}/verify", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == "verified"
        assert res.json()["paid_at"] is not None

    def test_unlinked_payment_can_be_rejected_by_owner(self, auth_seller_a, mock_db):
        """Owner can reject an unlinked payment."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="700.00", pay_status="pending"))

        res = client.post(f"/api/payments/{pid}/reject", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == "rejected"

    def test_rejected_payment_cannot_transition_to_verified(self, auth_seller_a, mock_db):
        """Terminal rejected status cannot be transitioned to verified (400 Bad Request)."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="700.00", pay_status="rejected"))

        res = client.post(f"/api/payments/{pid}/verify", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# 8. Seller Isolation on Unlinked Payments
# ============================================================================

class TestSellerIsolationOnUnlinkedPayments:
    def test_seller_b_cannot_view_seller_a_unlinked_payment(self, mock_db):
        """Seller B receives 404 when querying Seller A's unlinked payment."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="900.00"))

        seller_b = AuthenticatedSeller(id=SELLER_B_ID, db=mock_db)
        app.dependency_overrides[get_current_seller] = lambda: seller_b

        res = client.get(f"/api/payments/{pid}", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_seller_b_cannot_link_seller_a_unlinked_payment(self, mock_db):
        """Seller B cannot link Seller A's unlinked payment (404 Not Found)."""
        pid = str(uuid.uuid4())
        mock_db.store["payments"].append(make_payment_dict(pid=pid, order_id=None, amount="900.00"))

        seller_b_order = str(uuid.uuid4())
        mock_db.store["orders"].append(make_order_dict(oid=seller_b_order, seller_id=SELLER_B_ID, total_amount="900.00"))

        seller_b = AuthenticatedSeller(id=SELLER_B_ID, db=mock_db)
        app.dependency_overrides[get_current_seller] = lambda: seller_b

        res = client.post(
            f"/api/payments/{pid}/link",
            json={"order_id": seller_b_order},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# 9. Probe Error Classification Unit Tests
# ============================================================================

class TestProbeErrorClassification:
    """Verifies that check_is_order_id_nullable_live only classifies 23502 on order_id as not deployed."""

    def test_23502_on_order_id_returns_false(self):
        from postgrest.exceptions import APIError
        from tests.test_live_phase3f_unlinked_payments import classify_probe_error

        err = APIError({
            "code": "23502",
            "message": 'null value in column "order_id" of relation "payments" violates not-null constraint',
            "details": "Failing row contains (null, ...).",
            "hint": None,
        })
        assert classify_probe_error(err) is False

    def test_23502_on_other_column_raises_runtime_error(self):
        from postgrest.exceptions import APIError
        from tests.test_live_phase3f_unlinked_payments import classify_probe_error

        err = APIError({
            "code": "23502",
            "message": 'null value in column "seller_id" of relation "payments" violates not-null constraint',
            "details": None,
            "hint": None,
        })
        with pytest.raises(RuntimeError, match="Unexpected database error"):
            classify_probe_error(err)

    def test_missing_column_pgrst204_raises_runtime_error(self):
        from postgrest.exceptions import APIError
        from tests.test_live_phase3f_unlinked_payments import classify_probe_error

        err = APIError({
            "code": "PGRST204",
            "message": "Could not find the 'currency' column of 'payments' in the schema cache",
            "details": None,
            "hint": None,
        })
        with pytest.raises(RuntimeError, match="Unexpected database error"):
            classify_probe_error(err)

    def test_rls_error_42501_raises_runtime_error(self):
        from postgrest.exceptions import APIError
        from tests.test_live_phase3f_unlinked_payments import classify_probe_error

        err = APIError({
            "code": "42501",
            "message": 'new row violates row-level security policy for table "payments"',
            "details": None,
            "hint": None,
        })
        with pytest.raises(RuntimeError, match="Unexpected database error"):
            classify_probe_error(err)

    def test_generic_exception_raises_runtime_error(self):
        from tests.test_live_phase3f_unlinked_payments import classify_probe_error

        err = ConnectionError("Failed to reach Supabase API host")
        with pytest.raises(RuntimeError, match="Unexpected database error"):
            classify_probe_error(err)

