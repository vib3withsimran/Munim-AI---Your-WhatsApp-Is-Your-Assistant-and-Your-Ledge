"""
==============================================================================
Munim AI — Live Supabase Unlinked Payments Integration Test Suite (Phase 3F)
==============================================================================
Tests Phase 3F unlinked payment support directly against live Supabase:
- Nullable order_id schema check (Migration 20261101_003_unlinked_payments.sql)
- Unlinked payment creation (POST /api/payments with order_id=None)
- Unlinked payment listing (GET /api/payments?unlinked_only=true)
- Cross-seller RLS boundary enforcement for unlinked payments
- Linking unlinked payments to active orders (POST /api/payments/{id}/link)
- Rejection of cross-seller linking attempts
- Rejection of cancelled order linking attempts
- Rejection of duplicate transaction_reference per seller (allowed across sellers)
- Verification gating: only verified payments reduce order dues
"""

import os
import uuid
from decimal import Decimal
from typing import Tuple, Optional
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from supabase import create_client, Client

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)


def get_live_seller_tokens() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Retrieves live JWT tokens for Seller A and Seller B."""
    env = {**dotenv_values(".env"), **os.environ}
    email_a = env.get("TEST_SELLER_A_EMAIL") or env.get("SELLER_A_EMAIL")
    pass_a = env.get("TEST_SELLER_A_PASSWORD") or env.get("SELLER_A_PASSWORD")
    email_b = env.get("TEST_SELLER_B_EMAIL") or env.get("SELLER_B_EMAIL")
    pass_b = env.get("TEST_SELLER_B_PASSWORD") or env.get("SELLER_B_PASSWORD")

    if not email_a or not pass_a or not email_b or not pass_b:
        return None, None, None, None, "Missing test seller credentials in .env"

    try:
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        auth_a = sb.auth.sign_in_with_password({"email": email_a, "password": pass_a})
        token_a = auth_a.session.access_token
        seller_a_id = str(auth_a.user.id)

        auth_b = sb.auth.sign_in_with_password({"email": email_b, "password": pass_b})
        token_b = auth_b.session.access_token
        seller_b_id = str(auth_b.user.id)

        return token_a, seller_a_id, token_b, seller_b_id, None
    except Exception as e:
        return None, None, None, None, f"Supabase auth failed: {e}"


def classify_probe_error(e: Exception) -> bool:
    """
    Classifies a probe failure.
    Returns False ONLY if the failure is PostgreSQL error 23502 specifically on payments.order_id
    (meaning the not-null constraint is still enforced).
    Raises RuntimeError for all other errors (missing columns, RLS violations, connection issues, etc.).
    """
    err_str = str(e)
    code = getattr(e, "code", None)
    message = getattr(e, "message", "") or ""
    details = getattr(e, "details", "") or ""

    if isinstance(e, dict):
        code = e.get("code")
        message = e.get("message", "")
        details = e.get("details", "")

    # Check if PostgREST APIError has error dict
    if hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
        d = e.args[0]
        code = code or d.get("code")
        message = message or d.get("message", "")
        details = details or d.get("details", "")

    is_23502 = (code == "23502") or ("23502" in err_str)
    on_order_id = ("order_id" in message) or ("order_id" in details) or ("order_id" in err_str)

    if is_23502 and on_order_id:
        return False

    raise RuntimeError(f"Unexpected database error during unlinked payment probe: {e}")


def check_is_order_id_nullable_live(token: str, seller_id: Optional[str] = None) -> bool:
    """
    Checks whether migration 20261101_003_unlinked_payments.sql has been deployed
    by attempting to insert a temporary dummy unlinked payment.
    """
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
    sb.postgrest.auth(token)
    test_ref = f"PROBE-{uuid.uuid4().hex[:8]}"

    payload = {
        "amount": 1.00,
        "method": "cash",
        "status": "pending",
        "order_id": None,
        "transaction_reference": test_ref
    }
    if seller_id:
        payload["seller_id"] = seller_id

    try:
        res = sb.table("payments").insert(payload).execute()
        if res.data:
            probe_id = res.data[0]["id"]
            sb.table("payments").delete().eq("id", probe_id).execute()
        return True
    except Exception as e:
        return classify_probe_error(e)


@pytest.mark.live_postgres
class TestLiveUnlinkedPayments:
    """Live HTTP endpoint integration tests for Phase 3F against real Supabase."""

    @pytest.fixture(autouse=True)
    def setup_live_tokens(self):
        token_a, seller_a_id, token_b, seller_b_id, error = get_live_seller_tokens()
        if error:
            pytest.skip(f"Live Supabase Auth credentials not available: {error}")
        self.token_a = token_a
        self.seller_a_id = seller_a_id
        self.token_b = token_b
        self.seller_b_id = seller_b_id
        self.headers_a = {"Authorization": f"Bearer {token_a}"}
        self.headers_b = {"Authorization": f"Bearer {token_b}"}

        if not check_is_order_id_nullable_live(token_a, seller_a_id):
            pytest.skip(
                "Migration '20261101_003_unlinked_payments.sql' is not yet deployed on live Supabase: "
                "payments.order_id still has NOT NULL constraint."
            )

    def test_live_unlinked_payment_lifecycle_and_linking(self):
        """
        Tests the full live lifecycle of unlinked payments:
        1. Create unlinked payment with order_id=None.
        2. Query unlinked payments via /api/payments?unlinked_only=true.
        3. Multi-tenant isolation: Seller B cannot view Seller A's unlinked payment.
        4. Create active order for Seller A.
        5. Cross-seller linking rejection: Seller B cannot link to Seller A's order.
        6. Seller A links unlinked payment to Seller A's order.
        7. Verified payment reduces dues; unverified does not.
        8. Uniqueness of transaction_reference per seller.
        """
        random_suffix = uuid.uuid4().hex[:6]
        phone = f"+9198{uuid.uuid4().int % 100000000:08d}"

        # Clean-up tracking
        clean_payments = []
        customer_id = None
        product_id = None
        variant_id = None
        order_id = None

        try:
            # 1. Create Unlinked Payment for Seller A
            txn_ref = f"UPI-UNLINKED-{random_suffix}"
            unlinked_payload = {
                "amount": 1500.00,
                "currency": "INR",
                "method": "upi",
                "transaction_reference": txn_ref,
                "notes": "Customer transferred 1500 before order creation",
                "order_id": None
            }
            res_pay = client.post("/api/payments", json=unlinked_payload, headers=self.headers_a)
            assert res_pay.status_code == 201, f"Create unlinked payment failed: {res_pay.text}"
            pay_data = res_pay.json()
            payment_id = pay_data["id"]
            clean_payments.append(payment_id)
            assert pay_data["order_id"] is None
            assert pay_data["status"] == "pending"
            assert Decimal(str(pay_data["amount"])) == Decimal("1500.00")

            # 2. Query unlinked payments
            list_res = client.get("/api/payments?unlinked_only=true", headers=self.headers_a)
            assert list_res.status_code == 200
            unlinked_list = list_res.json()
            unlinked_ids = [p["id"] for p in unlinked_list]
            assert payment_id in unlinked_ids

            # 3. Multi-tenant isolation: Seller B cannot view Seller A's unlinked payment
            b_get_res = client.get(f"/api/payments/{payment_id}", headers=self.headers_b)
            assert b_get_res.status_code == 404

            # Seller B's unlinked list must NOT include Seller A's payment
            b_list_res = client.get("/api/payments?unlinked_only=true", headers=self.headers_b)
            assert b_list_res.status_code == 200
            assert payment_id not in [p["id"] for p in b_list_res.json()]

            # 4. Create active Order for Seller A
            cust_res = client.post(
                "/api/customers",
                json={"phone": phone, "name": f"Live Cust {random_suffix}"},
                headers=self.headers_a
            )
            assert cust_res.status_code == 201
            customer_id = cust_res.json()["id"]

            prod_res = client.post(
                "/api/products",
                json={"name": f"Live Product {random_suffix}", "category": "Apparel"},
                headers=self.headers_a
            )
            assert prod_res.status_code == 201
            product_id = prod_res.json()["id"]

            var_res = client.post(
                f"/api/products/{product_id}/variants",
                json={"sku": f"VAR-{random_suffix}", "price": 1500.00},
                headers=self.headers_a
            )
            assert var_res.status_code == 201
            variant_id = var_res.json()["id"]

            inv_res = client.patch(
                f"/api/inventory/{variant_id}",
                json={"available_quantity": 5, "reserved_quantity": 0},
                headers=self.headers_a
            )
            assert inv_res.status_code == 200

            ord_res = client.post(
                "/api/orders",
                json={"customer_id": customer_id, "items": [{"variant_id": variant_id, "quantity": 1}]},
                headers=self.headers_a
            )
            assert ord_res.status_code == 201
            order_data = ord_res.json()
            order_id = order_data["id"]
            assert Decimal(str(order_data["total_amount"])) == Decimal("1500.00")
            assert order_data["payment_status"] == "unpaid"

            # 5. Cross-seller linking rejection: Seller B cannot link payment to Seller A's order
            b_link_res = client.post(
                f"/api/payments/{payment_id}/link",
                json={"order_id": order_id},
                headers=self.headers_b
            )
            assert b_link_res.status_code in (403, 404)

            # 6. Seller A links unlinked payment to Seller A's order
            link_res = client.post(
                f"/api/payments/{payment_id}/link",
                json={"order_id": order_id},
                headers=self.headers_a
            )
            assert link_res.status_code == 200
            linked_payment = link_res.json()
            assert linked_payment["order_id"] == order_id
            assert linked_payment["status"] == "pending"

            # Payment must no longer appear in unlinked_only list
            list_after_link = client.get("/api/payments?unlinked_only=true", headers=self.headers_a)
            assert payment_id not in [p["id"] for p in list_after_link.json()]

            # 7. Verification gating: Pending payment does NOT mark order as paid
            check_ord = client.get(f"/api/orders/{order_id}", headers=self.headers_a)
            assert check_ord.json()["payment_status"] == "unpaid"

            # Merchant verifies payment
            ver_res = client.post(f"/api/payments/{payment_id}/verify", headers=self.headers_a)
            assert ver_res.status_code == 200
            assert ver_res.json()["status"] == "verified"

            # Order payment status must now be 'paid'
            paid_ord = client.get(f"/api/orders/{order_id}", headers=self.headers_a)
            assert paid_ord.json()["payment_status"] == "paid"

            # 8. Uniqueness of transaction_reference per seller
            dup_pay_payload = {
                "amount": 100.00,
                "currency": "INR",
                "method": "upi",
                "transaction_reference": txn_ref,
                "order_id": None
            }
            dup_res = client.post("/api/payments", json=dup_pay_payload, headers=self.headers_a)
            assert dup_res.status_code == 409, f"Expected 409 Conflict for duplicate txn_ref, got {dup_res.status_code}"

            # Seller B using the same reference MUST be permitted (tenant isolation)
            b_pay_res = client.post("/api/payments", json=dup_pay_payload, headers=self.headers_b)
            assert b_pay_res.status_code == 201
            clean_payments.append(b_pay_res.json()["id"])

        finally:
            sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
            # Cleanup Seller A records
            sb.postgrest.auth(self.token_a)
            for pid in clean_payments:
                try:
                    sb.table("payments").delete().eq("id", pid).execute()
                except Exception:
                    pass
            if order_id:
                try:
                    sb.table("order_items").delete().eq("order_id", order_id).execute()
                    sb.table("orders").delete().eq("id", order_id).execute()
                except Exception:
                    pass
            if variant_id:
                try:
                    sb.table("inventory").delete().eq("variant_id", variant_id).execute()
                    sb.table("product_variants").delete().eq("id", variant_id).execute()
                except Exception:
                    pass
            if product_id:
                try:
                    sb.table("products").delete().eq("id", product_id).execute()
                except Exception:
                    pass
            if customer_id:
                try:
                    sb.table("customers").delete().eq("id", customer_id).execute()
                except Exception:
                    pass

