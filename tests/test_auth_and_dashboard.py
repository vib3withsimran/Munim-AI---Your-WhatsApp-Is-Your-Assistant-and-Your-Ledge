import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from backend.app.main import app
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.models.auth_schemas import SignupResponse, LoginResponse

client = TestClient(app)


# ============================================================================
# Mock Helpers for Supabase Auth & PostgREST Database
# ============================================================================

class MockPostgrestQuery:
    def __init__(self, data: list, seller_id: str = None):
        self._data = list(data)
        self._seller_id = seller_id

    def select(self, *args, **kwargs):
        return self

    def eq(self, column: str, value: str):
        self._data = [row for row in self._data if row.get(column) == value]
        return self

    def in_(self, column: str, values: list):
        self._data = [row for row in self._data if row.get(column) in values]
        return self

    def gte(self, column: str, value: str):
        self._data = [row for row in self._data if str(row.get(column, "")) >= str(value)]
        return self

    def lte(self, column: str, value: str):
        self._data = [row for row in self._data if str(row.get(column, "")) <= str(value)]
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, limit_val: int):
        self._data = self._data[:limit_val]
        return self

    def maybe_single(self):
        return self

    def single(self):
        return self

    def update(self, update_dict: dict):
        for row in self._data:
            row.update(update_dict)
        return self

    def upsert(self, upsert_dict: dict, *args, **kwargs):
        self._data.append(upsert_dict)
        return self

    def execute(self):
        mock_res = MagicMock()
        mock_res.data = self._data
        return mock_res


class MockPostgrestClient:
    def __init__(self, in_memory_db: dict, seller_id: str):
        self.in_memory_db = in_memory_db
        self.seller_id = seller_id

    def table(self, table_name: str):
        rows = self.in_memory_db.get(table_name, [])
        return MockPostgrestQuery(rows, self.seller_id)


class MockSellerDb:
    def __init__(self, in_memory_db: dict, seller_id: str):
        self.postgrest = MagicMock()
        self._db = MockPostgrestClient(in_memory_db, seller_id)
        self.auth = MagicMock()

    def table(self, table_name: str):
        return self._db.table(table_name)


# ============================================================================
# Authentication Endpoint Tests
# ============================================================================

def test_signup_valid_input_email_confirmation_required():
    """Signup with valid details returns 201 with email_verification_required=True when no session is returned."""
    mock_user = MagicMock()
    mock_user.id = "seller-uuid-123"
    mock_user.email = "seller@example.com"
    mock_user.identities = ["identity-1"]

    mock_auth_res = MagicMock()
    mock_auth_res.user = mock_user
    mock_auth_res.session = None  # Email confirmation enabled: no session on signup

    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.sign_up.return_value = mock_auth_res
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/signup",
            json={
                "email": "seller@example.com",
                "password": "securepassword123",
                "business_name": "Neha's Boutique",
                "phone": "919876543210",
                "business_type": "Retail Clothing"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["email_verification_required"] is True
        assert data["seller_id"] == "seller-uuid-123"
        assert "verify your email" in data["message"].lower()


def test_signup_invalid_input():
    """Signup with invalid email and too-short password returns 422 Unprocessable Entity."""
    response = client.post(
        "/auth/signup",
        json={
            "email": "not-an-email",
            "password": "123",  # Under 6 chars
            "business_name": ""  # Empty
        }
    )
    assert response.status_code == 422


def test_signup_duplicate_email():
    """Duplicate email registration returns 400 Bad Request."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.sign_up.side_effect = AuthApiError(
            message="User already registered",
            status=400,
            code="user_already_exists"
        )
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/signup",
            json={
                "email": "existing@example.com",
                "password": "securepassword123",
                "business_name": "Existing Store"
            }
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()


def test_login_valid_credentials():
    """Valid login credentials return 200 with tokens and seller profile information."""
    mock_user = MagicMock()
    mock_user.id = "seller-uuid-123"
    mock_user.email = "seller@example.com"
    mock_user.user_metadata = {"business_name": "Neha's Boutique"}

    mock_session = MagicMock()
    mock_session.access_token = "valid_access_token_123"
    mock_session.refresh_token = "valid_refresh_token_123"
    mock_session.expires_in = 3600
    mock_session.expires_at = 1730419200

    mock_auth_res = MagicMock()
    mock_auth_res.user = mock_user
    mock_auth_res.session = mock_session

    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client, \
         patch("backend.app.api.routes.auth.create_client") as mock_create_client:

        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.return_value = mock_auth_res
        mock_get_client.return_value = mock_client

        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
            "business_name": "Neha's Boutique",
            "phone": "919876543210",
            "business_type": "Clothing"
        }
        mock_create_client.return_value = mock_db

        response = client.post(
            "/auth/login",
            json={
                "email": "seller@example.com",
                "password": "validpassword"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "valid_access_token_123"
        assert data["seller"]["id"] == "seller-uuid-123"
        assert data["seller"]["business_name"] == "Neha's Boutique"


def test_login_unconfirmed_email():
    """Unconfirmed email login attempt returns 403 Forbidden with prompt to verify email."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError(
            message="Email not confirmed",
            status=400,
            code="email_not_confirmed"
        )
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/login",
            json={
                "email": "unverified@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 403
        assert "email verification required" in response.json()["detail"].lower()


def test_login_invalid_credentials():
    """Invalid email or password returns 401 Unauthorized."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError(
            message="Invalid login credentials",
            status=400,
            code="invalid_credentials"
        )
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/login",
            json={
                "email": "seller@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid email or password" in response.json()["detail"].lower()


def test_missing_bearer_token():
    """Accessing protected endpoint /auth/me without Bearer token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert "authentication required" in response.json()["detail"].lower()


def test_invalid_bearer_token():
    """Accessing protected endpoint with invalid Bearer token returns 401."""
    with patch("backend.app.core.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.get_user.side_effect = AuthApiError(
            message="Invalid token",
            status=401,
            code="invalid_token"
        )
        mock_get_client.return_value = mock_client

        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer bad_token_123"}
        )
        assert response.status_code == 401
        assert "invalid or expired" in response.json()["detail"].lower()


def test_get_auth_me_success():
    """GET /auth/me returns authenticated seller profile."""
    seller_id = "seller-uuid-abc"
    in_memory = {
        "profiles": [
            {
                "id": seller_id,
                "business_name": "Riya Garments",
                "phone": "919999988888",
                "business_type": "Apparel",
                "created_at": "2026-10-01T10:00:00Z",
                "updated_at": "2026-10-01T10:00:00Z"
            }
        ]
    }
    mock_db = MockSellerDb(in_memory, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        response = client.get("/auth/me", headers={"Authorization": "Bearer dummy"})
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == seller_id
        assert data["business_name"] == "Riya Garments"
        assert data["phone"] == "919999988888"
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_patch_auth_me_profile_update():
    """PATCH /auth/me updates allowed seller profile fields only."""
    seller_id = "seller-uuid-abc"
    in_memory = {
        "profiles": [
            {
                "id": seller_id,
                "business_name": "Old Name",
                "phone": "919999988888",
                "business_type": "Retail"
            }
        ]
    }
    mock_db = MockSellerDb(in_memory, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        response = client.patch(
            "/auth/me",
            headers={"Authorization": "Bearer dummy"},
            json={
                "business_name": "New Modern Boutique",
                "phone": "919111122222"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["business_name"] == "New Modern Boutique"
        assert data["phone"] == "919111122222"
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_reset_password_endpoint():
    """POST /auth/reset-password returns generic 200 without exposing email existence."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/reset-password",
            json={"email": "anyuser@example.com"}
        )
        assert response.status_code == 200
        assert "password reset link has been dispatched" in response.json()["message"]


# ============================================================================
# Dashboard Endpoint Tests & Business Calculation Rules
# ============================================================================

def test_dashboard_unauthenticated_receives_401():
    """Unauthenticated requests to all dashboard endpoints receive 401."""
    assert client.get("/dashboard/summary").status_code == 401
    assert client.get("/dashboard/sales").status_code == 401
    assert client.get("/dashboard/activity").status_code == 401
    assert client.get("/dashboard/breakdown").status_code == 401


def test_dashboard_empty_database_returns_valid_empty_structure():
    """Empty database returns valid zeroed structures without errors."""
    seller_id = "empty-seller-uuid"
    empty_db = {
        "orders": [],
        "payments": [],
        "order_items": [],
        "customers": [],
        "agent_logs": []
    }
    mock_db = MockSellerDb(empty_db, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        summary_res = client.get("/dashboard/summary", headers={"Authorization": "Bearer dummy"})
        assert summary_res.status_code == 200
        summary_data = summary_res.json()
        assert summary_data["revenue"]["value"] == 0.0
        assert summary_data["orders"]["value"] == 0.0
        assert summary_data["pending_dues"]["value"] == 0.0
        assert len(summary_data["stats"]) == 4

        sales_res = client.get("/dashboard/sales?period=7D", headers={"Authorization": "Bearer dummy"})
        assert sales_res.status_code == 200
        sales_data = sales_res.json()
        assert sales_data["total_sales"] == 0.0
        assert len(sales_data["data"]) == 7

        activity_res = client.get("/dashboard/activity", headers={"Authorization": "Bearer dummy"})
        assert activity_res.status_code == 200
        activity_data = activity_res.json()
        assert len(activity_data["activities"]) == 5
        assert activity_data["memories"] == []

        breakdown_res = client.get("/dashboard/breakdown", headers={"Authorization": "Bearer dummy"})
        assert breakdown_res.status_code == 200
        breakdown_data = breakdown_res.json()
        assert breakdown_data["total_orders"] == 0
        assert breakdown_data["top_products"] == []
        assert breakdown_data["pending_dues"] == []
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_two_seller_rls_tenant_isolation():
    """
    Genuine multi-tenant isolation test:
    Database contains records for both Seller A and Seller B.
    Seller A must only receive Seller A's data, never Seller B's data.
    """
    seller_a_id = "seller-a"
    seller_b_id = "seller-b"

    now_iso = datetime.now(timezone.utc).isoformat()

    shared_db = {
        "orders": [
            {"id": "ord-a1", "seller_id": seller_a_id, "customer_id": "cust-a", "status": "completed", "total_amount": 1000.0, "created_at": now_iso},
            {"id": "ord-b1", "seller_id": seller_b_id, "customer_id": "cust-b", "status": "completed", "total_amount": 50000.0, "created_at": now_iso},
        ],
        "payments": [
            {"id": "pay-a1", "seller_id": seller_a_id, "order_id": "ord-a1", "amount": 1000.0, "status": "verified", "created_at": now_iso, "paid_at": now_iso},
            {"id": "pay-b1", "seller_id": seller_b_id, "order_id": "ord-b1", "amount": 50000.0, "status": "verified", "created_at": now_iso, "paid_at": now_iso},
        ],
        "customers": [
            {"id": "cust-a", "seller_id": seller_a_id, "name": "Buyer A", "phone": "910000000001"},
            {"id": "cust-b", "seller_id": seller_b_id, "name": "Buyer B", "phone": "910000000002"},
        ],
        "order_items": [
            {"seller_id": seller_a_id, "product_name_snapshot": "Seller A Kurti", "quantity": 1, "unit_price": 1000.0, "line_total": 1000.0},
            {"seller_id": seller_b_id, "product_name_snapshot": "Seller B Lehenga", "quantity": 10, "unit_price": 5000.0, "line_total": 50000.0},
        ],
        "agent_logs": []
    }

    # Query as Seller A
    mock_db_a = MockSellerDb(shared_db, seller_a_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_a_id, db=mock_db_a)

    try:
        summary_res = client.get("/dashboard/summary", headers={"Authorization": "Bearer dummy"})
        assert summary_res.status_code == 200
        data_a = summary_res.json()

        # Seller A's revenue must be exactly 1000, NOT 51000
        assert data_a["revenue"]["value"] == 1000.0
        assert data_a["orders"]["value"] == 1.0

        # Breakdown test for Seller A
        breakdown_res = client.get("/dashboard/breakdown", headers={"Authorization": "Bearer dummy"})
        assert breakdown_res.status_code == 200
        bd_a = breakdown_res.json()
        assert len(bd_a["top_products"]) == 1
        assert bd_a["top_products"][0]["name"] == "Seller A Kurti"
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_dues_calculation_unverified_payments_do_not_reduce_dues():
    """
    Calculation rule verification:
    Order total is 1000.
    Unverified or rejected payment of 400 does NOT reduce dues (due remains 1000).
    Verified payment of 600 reduces due to 400.
    """
    seller_id = "test-dues-seller"
    now_iso = datetime.now(timezone.utc).isoformat()

    db_state = {
        "orders": [
            {"id": "ord-1", "seller_id": seller_id, "customer_id": "cust-1", "status": "processing", "total_amount": 1000.0, "created_at": now_iso}
        ],
        "payments": [
            # Unverified payment: must be ignored when calculating dues
            {"id": "pay-1", "seller_id": seller_id, "order_id": "ord-1", "amount": 400.0, "status": "pending", "created_at": now_iso},
            # Rejected payment: must be ignored when calculating dues
            {"id": "pay-2", "seller_id": seller_id, "order_id": "ord-1", "amount": 200.0, "status": "rejected", "created_at": now_iso},
            # Verified payment: genuinely reduces dues
            {"id": "pay-3", "seller_id": seller_id, "order_id": "ord-1", "amount": 300.0, "status": "verified", "created_at": now_iso}
        ],
        "customers": [
            {"id": "cust-1", "seller_id": seller_id, "name": "Simran Kaur", "phone": "919876500000"}
        ],
        "order_items": [],
        "agent_logs": []
    }

    mock_db = MockSellerDb(db_state, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        summary_res = client.get("/dashboard/summary", headers={"Authorization": "Bearer dummy"})
        assert summary_res.status_code == 200
        data = summary_res.json()

        # Total is 1000. Only 300 is verified. Dues must be 700 (NOT 100).
        assert data["pending_dues"]["value"] == 700.0
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_cancelled_orders_not_counted_as_revenue():
    """
    Calculation rule verification:
    Cancelled orders and any payments linked to them are NOT counted in revenue.
    """
    seller_id = "test-cancelled-seller"
    now_iso = datetime.now(timezone.utc).isoformat()

    db_state = {
        "orders": [
            {"id": "ord-cancelled", "seller_id": seller_id, "customer_id": "cust-1", "status": "cancelled", "total_amount": 2500.0, "created_at": now_iso},
            {"id": "ord-active", "seller_id": seller_id, "customer_id": "cust-1", "status": "completed", "total_amount": 800.0, "created_at": now_iso}
        ],
        "payments": [
            # Payment for cancelled order: must NOT be counted
            {"id": "pay-canc", "seller_id": seller_id, "order_id": "ord-cancelled", "amount": 2500.0, "status": "verified", "created_at": now_iso, "paid_at": now_iso},
            # Payment for active order: counted
            {"id": "pay-act", "seller_id": seller_id, "order_id": "ord-active", "amount": 800.0, "status": "verified", "created_at": now_iso, "paid_at": now_iso}
        ],
        "customers": [],
        "order_items": [],
        "agent_logs": []
    }

    mock_db = MockSellerDb(db_state, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        summary_res = client.get("/dashboard/summary", headers={"Authorization": "Bearer dummy"})
        assert summary_res.status_code == 200
        data = summary_res.json()

        # Revenue must ONLY be 800 (cancelled 2500 excluded)
        assert data["revenue"]["value"] == 800.0
        # Orders count must exclude cancelled: 1 order
        assert data["orders"]["value"] == 1.0
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_sales_invalid_period_rejected():
    """GET /dashboard/sales with an unsupported period parameter returns 400 Bad Request."""
    seller_id = "test-sales-seller"
    mock_db = MockSellerDb({}, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        response = client.get("/dashboard/sales?period=1YEAR", headers={"Authorization": "Bearer dummy"})
        assert response.status_code == 400
        assert "invalid period" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_dashboard_sales_all_valid_periods():
    """GET /dashboard/sales works for all supported periods: 7D, 30D, 3M, 6M."""
    seller_id = "test-periods-seller"
    mock_db = MockSellerDb({}, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        for p in ["7D", "30D", "3M", "6M"]:
            res = client.get(f"/dashboard/sales?period={p}", headers={"Authorization": "Bearer dummy"})
            assert res.status_code == 200
            data = res.json()
            assert data["period"] == p
            assert isinstance(data["data"], list)
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_dashboard_activity_with_agent_logs():
    """GET /dashboard/activity aggregates messages, reminders, orders, and memory highlights."""
    seller_id = "test-activity-seller"
    now_iso = datetime.now(timezone.utc).isoformat()

    db_state = {
        "orders": [
            {"id": "ord-1", "seller_id": seller_id, "created_at": now_iso}
        ],
        "payments": [
            {"id": "pay-1", "seller_id": seller_id, "created_at": now_iso}
        ],
        "agent_logs": [
            {
                "id": "log-1",
                "seller_id": seller_id,
                "agent_name": "Munim AI",
                "action": "message_received",
                "entity_type": "message",
                "created_at": now_iso
            },
            {
                "id": "log-2",
                "seller_id": seller_id,
                "agent_name": "Munim Memory",
                "action": "memory_update",
                "entity_type": "memory",
                "meko_operation": "upsert",
                "metadata": {"summary": "Priya prefers size M kurtis", "source": "Updated today"},
                "created_at": now_iso
            }
        ]
    }

    mock_db = MockSellerDb(db_state, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        res = client.get("/dashboard/activity", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == 200
        data = res.json()
        assert data["orders_created_count"] == 1
        assert data["payments_received_count"] == 1
        assert data["new_messages_count"] == 1
        assert data["memories_updated_count"] == 1
        assert len(data["memories"]) == 1
        assert "Priya prefers" in data["memories"][0]["text"]
    finally:
        app.dependency_overrides.pop(get_current_seller, None)


def test_dashboard_breakdown_aggregations():
    """GET /dashboard/breakdown aggregates order status counts, top products, and customer dues."""
    seller_id = "test-bd-seller"
    now_iso = datetime.now(timezone.utc).isoformat()

    db_state = {
        "orders": [
            {"id": "o1", "seller_id": seller_id, "customer_id": "c1", "status": "completed", "total_amount": 1500.0, "created_at": now_iso},
            {"id": "o2", "seller_id": seller_id, "customer_id": "c2", "status": "processing", "total_amount": 2000.0, "created_at": now_iso},
            {"id": "o3", "seller_id": seller_id, "customer_id": "c2", "status": "cancelled", "total_amount": 500.0, "created_at": now_iso},
        ],
        "payments": [
            {"id": "p1", "seller_id": seller_id, "order_id": "o1", "amount": 1500.0, "status": "verified", "created_at": now_iso},
            {"id": "p2", "seller_id": seller_id, "order_id": "o2", "amount": 500.0, "status": "verified", "created_at": now_iso},
        ],
        "order_items": [
            {"seller_id": seller_id, "product_name_snapshot": "Pink Anarkali", "quantity": 3, "unit_price": 500.0, "line_total": 1500.0},
            {"seller_id": seller_id, "product_name_snapshot": "Blue Kurti", "quantity": 2, "unit_price": 1000.0, "line_total": 2000.0},
        ],
        "customers": [
            {"id": "c1", "seller_id": seller_id, "name": "Aditi Rao", "phone": "919876543210"},
            {"id": "c2", "seller_id": seller_id, "name": "Kavita Sharma", "phone": "919812345678"},
        ],
        "agent_logs": []
    }

    mock_db = MockSellerDb(db_state, seller_id)
    app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(id=seller_id, db=mock_db)

    try:
        res = client.get("/dashboard/breakdown", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == 200
        data = res.json()

        assert data["total_orders"] == 3
        # Check order status list
        statuses = {s["label"]: s["value"] for s in data["order_statuses"]}
        assert statuses["Completed"] == 1
        assert statuses["Processing"] == 1
        assert statuses["Cancelled"] == 1

        # Check top products
        assert len(data["top_products"]) == 2
        assert data["top_products"][0]["name"] == "Pink Anarkali"  # sold 3 > 2

        # Check pending dues: c2 has order o2 total 2000 - 500 = 1500 due (cancelled o3 excluded)
        assert len(data["pending_dues"]) == 1
        due_cust = data["pending_dues"][0]
        assert due_cust["name"] == "Kavita Sharma"
        assert due_cust["initials"] == "KS"
        assert due_cust["amount"] == 1500.0
        assert due_cust["orders"] == 1
    finally:
        app.dependency_overrides.pop(get_current_seller, None)
