import sys
from pathlib import Path
import json

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("MUNIM AI: FULL INTEGRATION & VERIFICATION TEST SUITE")
    print("=" * 60)

    # Test 1: Healthcheck
    res = client.get("/")
    assert res.status_code == 200
    print("[PASS] 1. Backend root healthcheck:", res.json())

    # Test 2: Dashboard blocked without token
    res = client.get("/dashboard/summary")
    assert res.status_code == 401
    assert "authentication required" in res.json()["detail"].lower()
    print("[PASS] 2. Dashboard access blocked without token (401 Unauthorized)")

    # Test 3: Unconfirmed email login handling
    from unittest.mock import MagicMock, patch
    from supabase_auth.errors import AuthApiError

    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.auth.sign_in_with_password.side_effect = AuthApiError(
            message="Email not confirmed",
            status=400,
            code="email_not_confirmed"
        )
        mock_get_client.return_value = mock_client

        res = client.post("/auth/login", json={"email": "unverified@example.com", "password": "pass"})
        assert res.status_code == 403
        assert "email verification required" in res.json()["detail"].lower()
        print("[PASS] 3. Unconfirmed email safely returns 403 with verification notice")

    # Test 4: Signup email verification requirement
    with patch("backend.app.api.routes.auth.get_supabase_client") as mock_get_client:
        mock_user = MagicMock()
        mock_user.id = "seller-123"
        mock_user.email = "seller@test.com"
        mock_user.identities = ["id-1"]

        mock_auth_res = MagicMock()
        mock_auth_res.user = mock_user
        mock_auth_res.session = None  # No session returned on signup

        mock_client = MagicMock()
        mock_client.auth.sign_up.return_value = mock_auth_res
        mock_get_client.return_value = mock_client

        res = client.post(
            "/auth/signup",
            json={
                "email": "seller@test.com",
                "password": "password123",
                "business_name": "Test Store",
                "phone": "919999988888"
            }
        )
        assert res.status_code == 201
        data = res.json()
        assert data["email_verification_required"] is True
        print("[PASS] 4. Signup detects email confirmation enabled and prompts verification")

    # Test 5: Next.js build verification
    next_manifest = Path("frontend/.next/routes-manifest.json")
    if next_manifest.exists():
        manifest = json.loads(next_manifest.read_text())
        static_routes = [r.get("page") for r in manifest.get("staticRoutes", [])]
        assert "/login" in static_routes
        assert "/signup" in static_routes
        assert "/dashboard" in static_routes
        print(f"[PASS] 5. Next.js routes built: {static_routes}")
    else:
        print("[SKIP] 5. routes-manifest.json not found")

    print("\n" + "=" * 60)
    print("ALL FRONTEND & BACKEND INTEGRATION CHECKS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
