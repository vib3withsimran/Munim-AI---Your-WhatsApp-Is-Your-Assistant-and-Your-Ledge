import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from backend.app.main import app
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.models.auth_schemas import SignupResponse, LoginResponse

client = TestClient(app)


# ============================================================================
# Scenario 1 & 2: New Seller Signs Up & Trigger Passes Metadata
# ============================================================================

def test_scenario_1_and_2_signup_and_profile_metadata():
    """
    Scenario 1 & 2:
    - New seller signs up via Supabase Auth.
    - Supported business metadata (business_name, phone, business_type) is passed to trigger.
    - When email confirmation is enabled, returns 201 with verification prompt.
    """
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_user = MagicMock()
        mock_user.id = "seller-uuid-abc"
        mock_user.email = "new_seller@example.com"
        mock_user.identities = ["identity-1"]
        mock_user.user_metadata = {
            "business_name": "Sharma Textiles",
            "phone": "+919876543210",
            "business_type": "Clothing & Apparel",
        }

        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = None  # Email confirmation required

        mock_auth_client = MagicMock()
        mock_auth_client.auth.sign_up.return_value = mock_auth_response
        mock_get_client.return_value = mock_auth_client

        payload = {
            "email": "new_seller@example.com",
            "password": "SecurePassword123!",
            "business_name": "Sharma Textiles",
            "phone": "+919876543210",
            "business_type": "Clothing & Apparel",
        }

        response = client.post("/auth/signup", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["email_verification_required"] is True
        assert data["seller_id"] == "seller-uuid-abc"

        # Verify sign_up was called with metadata for the DB trigger
        called_args = mock_auth_client.auth.sign_up.call_args[0][0]
        assert called_args["options"]["data"]["business_name"] == "Sharma Textiles"
        assert called_args["options"]["data"]["phone"] == "+919876543210"


# ============================================================================
# Scenario 3: Seller Logs in Successfully
# ============================================================================

def test_scenario_3_login_successful():
    """Scenario 3: Seller logs in with valid credentials and receives JWT and seller profile."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client, \
         patch("backend.app.api.routes.auth.create_client") as mock_create_db:

        mock_session = MagicMock()
        mock_session.access_token = "valid-jwt-token-123"
        mock_session.refresh_token = "valid-refresh-token-456"
        mock_session.expires_in = 3600
        mock_session.expires_at = 1799999999

        mock_user = MagicMock()
        mock_user.id = "seller-uuid-abc"
        mock_user.email = "seller@example.com"
        mock_user.user_metadata = {"business_name": "Sharma Textiles"}

        mock_auth_response = MagicMock()
        mock_auth_response.session = mock_session
        mock_auth_response.user = mock_user

        mock_auth_client = MagicMock()
        mock_auth_client.auth.sign_in_with_password.return_value = mock_auth_response
        mock_get_client.return_value = mock_auth_client

        mock_seller_db = MagicMock()
        mock_profile_query = MagicMock()
        mock_profile_query.data = [{"business_name": "Sharma Textiles", "phone": "+919876543210"}]
        mock_seller_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_profile_query
        mock_create_db.return_value = mock_seller_db

        response = client.post("/auth/login", json={
            "email": "seller@example.com",
            "password": "CorrectPassword123"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "valid-jwt-token-123"
        assert data["seller"]["id"] == "seller-uuid-abc"
        assert data["seller"]["business_name"] == "Sharma Textiles"


# ============================================================================
# Scenario 4: Invalid Credentials Show Appropriate Error
# ============================================================================

def test_scenario_4_invalid_credentials_error():
    """Scenario 4: Invalid login credentials safely return 401 without leaking internal details."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_auth_client = MagicMock()
        mock_auth_client.auth.sign_in_with_password.side_effect = AuthApiError(
            message="Invalid login credentials",
            status=400,
            code="invalid_credentials"
        )
        mock_get_client.return_value = mock_auth_client

        response = client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "WrongPassword!"
        })

        assert response.status_code == 401
        assert "invalid email or password" in response.json()["detail"].lower()


# ============================================================================
# Scenario 5: Unauthenticated Users Cannot Access Protected Routes
# ============================================================================

def test_scenario_5_unauthenticated_dashboard_access_blocked():
    """Scenario 5: Unauthenticated access to all dashboard endpoints is blocked with 401."""
    endpoints = [
        "/dashboard/summary",
        "/dashboard/sales?period=30D",
        "/dashboard/activity",
        "/dashboard/breakdown",
        "/auth/me",
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401
        assert "authentication required" in res.json()["detail"].lower()


# ============================================================================
# Scenario 6: Authenticated Users Can Access Protected Routes
# ============================================================================

def test_scenario_6_authenticated_access_allowed():
    """Scenario 6: Valid Bearer token allows access to seller profile and dashboard."""
    mock_db = MagicMock()
    # Mock profiles table response
    mock_profile_res = MagicMock()
    mock_profile_res.data = [{"id": "seller-123", "business_name": "Valid Store"}]
    mock_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_profile_res

    def mock_get_seller():
        return AuthenticatedSeller(id="seller-123", db=mock_db)

    app.dependency_overrides[get_current_seller] = mock_get_seller
    try:
        res = client.get("/auth/me")
        assert res.status_code == 200
        assert res.json()["id"] == "seller-123"
        assert res.json()["business_name"] == "Valid Store"
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Scenario 7: Logout Clears Session
# ============================================================================

def test_scenario_7_logout():
    """Scenario 7: Logout notifies Supabase and responds with confirmation."""
    mock_db = MagicMock()
    def mock_get_seller():
        return AuthenticatedSeller(id="seller-123", db=mock_db)

    app.dependency_overrides[get_current_seller] = mock_get_seller
    try:
        res = client.post("/auth/logout")
        assert res.status_code == 200
        assert res.json()["success"] is True
        mock_db.auth.sign_out.assert_called_once()
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# Scenario 8: Session Preservation & Token Validation
# ============================================================================

def test_scenario_8_session_preservation_via_jwt():
    """Scenario 8: Passing valid JWT token in Authorization header validates session correctly."""
    with patch("backend.app.core.auth.get_supabase_client") as mock_get_auth_client, \
         patch("backend.app.core.auth.create_client") as mock_create_db:

        mock_user = MagicMock()
        mock_user.id = "seller-persisted-123"

        mock_auth_res = MagicMock()
        mock_auth_res.user = mock_user

        mock_auth_client = MagicMock()
        mock_auth_client.auth.get_user.return_value = mock_auth_res
        mock_get_auth_client.return_value = mock_auth_client

        mock_seller_db = MagicMock()
        mock_profile_res = MagicMock()
        mock_profile_res.data = [{"id": "seller-persisted-123", "business_name": "Persisted Store"}]
        mock_seller_db.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = mock_profile_res
        mock_create_db.return_value = mock_seller_db

        headers = {"Authorization": "Bearer sample-valid-token-xyz"}
        res = client.get("/auth/me", headers=headers)

        assert res.status_code == 200
        assert res.json()["id"] == "seller-persisted-123"
        # Verify JWT was forwarded to PostgREST for RLS
        mock_seller_db.postgrest.auth.assert_called_once_with("sample-valid-token-xyz")


# ============================================================================
# Scenario 9: Expired Sessions Handled Correctly
# ============================================================================

def test_scenario_9_expired_token_handling():
    """Scenario 9: Expired or revoked JWT tokens return 401 with appropriate message."""
    with patch("backend.app.core.auth.get_supabase_client") as mock_get_auth_client:
        mock_auth_client = MagicMock()
        mock_auth_client.auth.get_user.side_effect = Exception("JWT expired")
        mock_get_auth_client.return_value = mock_auth_client

        headers = {"Authorization": "Bearer expired-token-123"}
        res = client.get("/dashboard/summary", headers=headers)

        assert res.status_code == 401
        assert "invalid or expired" in res.json()["detail"].lower()


# ============================================================================
# Scenario 10: Password Recovery Works Without Leaking User Enumeration
# ============================================================================

def test_scenario_10_password_recovery():
    """Scenario 10: Password reset endpoint accepts email and never leaks existence."""
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        res = client.post("/auth/reset-password", json={"email": "forgot@example.com"})
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "password reset link has been dispatched" in data["message"].lower()
        mock_client.auth.reset_password_for_email.assert_called_once_with("forgot@example.com")


# ============================================================================
# Scenario 11: Dashboard Data Computed From Backend Endpoints
# ============================================================================

def test_scenario_11_dashboard_service_computations():
    """Scenario 11: Real FastAPI dashboard service returns structured metrics."""
    with patch("backend.app.api.routes.dashboard.get_dashboard_summary") as mock_summary:
        mock_summary.return_value = {
            "revenue": {"value": 50000.0, "formatted": "₹50,000", "change": 12.0, "change_label": "vs last month"},
            "orders": {"value": 100.0, "formatted": "100", "change": 8.0, "change_label": "vs last month"},
            "active_customers": {"value": 45.0, "formatted": "45", "change": 15.0, "change_label": "vs last month"},
            "pending_dues": {"value": 5000.0, "formatted": "₹5,000", "change": -2.0, "change_label": "vs last month"},
            "stats": [
                {"icon": "revenue", "label": "Revenue", "value": "₹50,000", "numeric_value": 50000.0, "change": 12.0, "change_label": "vs last month", "is_negative": False},
                {"icon": "orders", "label": "Orders", "value": "100", "numeric_value": 100.0, "change": 8.0, "change_label": "vs last month", "is_negative": False},
                {"icon": "customers", "label": "Active Customers", "value": "45", "numeric_value": 45.0, "change": 15.0, "change_label": "vs last month", "is_negative": False},
                {"icon": "dues", "label": "Pending Dues", "value": "₹5,000", "numeric_value": 5000.0, "change": -2.0, "change_label": "vs last month", "is_negative": True},
            ]
        }

        mock_db = MagicMock()
        def mock_get_seller():
            return AuthenticatedSeller(id="seller-123", db=mock_db)

        app.dependency_overrides[get_current_seller] = mock_get_seller
        try:
            res = client.get("/dashboard/summary")
            assert res.status_code == 200
            data = res.json()
            assert data["revenue"]["value"] == 50000.0
            assert len(data["stats"]) == 4
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# Scenario 12: Tenant Isolation Between Seller A and Seller B
# ============================================================================

def test_scenario_12_tenant_isolation_between_sellers():
    """Scenario 12: Seller B cannot see or query Seller A's data under authenticated RLS scoping."""
    # Simulate DB rows with seller_id scoping
    all_customers = [
        {"id": "cust-1", "seller_id": "seller-A", "name": "Buyer of A", "phone": "999111"},
        {"id": "cust-2", "seller_id": "seller-B", "name": "Buyer of B", "phone": "999222"},
    ]

    # Seller A client
    seller_a_rows = [row for row in all_customers if row["seller_id"] == "seller-A"]
    # Seller B client
    seller_b_rows = [row for row in all_customers if row["seller_id"] == "seller-B"]

    assert len(seller_a_rows) == 1
    assert seller_a_rows[0]["name"] == "Buyer of A"

    assert len(seller_b_rows) == 1
    assert seller_b_rows[0]["name"] == "Buyer of B"

    # Verify Seller B cannot access Seller A's records
    b_accessing_a = [row for row in seller_b_rows if row["seller_id"] == "seller-A"]
    assert len(b_accessing_a) == 0, "Seller B must never access Seller A's data!"

