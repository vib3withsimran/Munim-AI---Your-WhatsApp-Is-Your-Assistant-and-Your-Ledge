"""
==============================================================================
Munim AI — Live Supabase FastAPI Endpoints Integration Test Suite (Phase 3E)
==============================================================================
Tests the Phase 3E FastAPI endpoints directly against live Supabase:
- Real Supabase Auth JWT validation
- Real PostgREST queries with seller-scoped tokens
- Real transactional RPC execution (create_order_with_reservation_rpc, fulfill_order_rpc)
- Cross-seller RLS boundary enforcement
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


@pytest.mark.live_postgres
class TestLiveFastAPIEndpoints:
    """Live HTTP endpoint integration tests against real Supabase instance."""

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

    def test_live_full_lifecycle_via_api(self):
        """
        Executes end-to-end commerce lifecycle on live Supabase via FastAPI endpoints:
        1. Create customer
        2. Create product & variant
        3. Set inventory
        4. Place order (invoking live create_order_with_reservation_rpc)
        5. Verify line items
        6. Cross-seller read rejection
        7. Fulfill order (invoking live fulfill_order_rpc)
        8. Record & verify payment
        """
        random_suffix = uuid.uuid4().hex[:6]
        phone = f"+9198{uuid.uuid4().int % 100000000:08d}"

        # 1. Customer
        cust_payload = {"phone": phone, "name": f"Live Test Customer {random_suffix}"}
        cust_res = client.post("/api/customers", json=cust_payload, headers=self.headers_a)
        assert cust_res.status_code == 201, f"Create customer failed: {cust_res.text}"
        customer_id = cust_res.json()["id"]

        product_id = None
        variant_id = None
        order_id = None
        payment_id = None

        try:
            # 2. Product
            prod_payload = {"name": f"Live Saree {random_suffix}", "category": "Test"}
            prod_res = client.post("/api/products", json=prod_payload, headers=self.headers_a)
            assert prod_res.status_code == 201, f"Create product failed: {prod_res.text}"
            product_id = prod_res.json()["id"]

            # Variant
            var_payload = {"sku": f"SAR-{random_suffix}", "price": 1250.00}
            var_res = client.post(f"/api/products/{product_id}/variants", json=var_payload, headers=self.headers_a)
            assert var_res.status_code == 201, f"Create variant failed: {var_res.text}"
            variant_id = var_res.json()["id"]

            # 3. Inventory
            inv_patch = {"available_quantity": 10, "reserved_quantity": 0, "low_stock_threshold": 2}
            inv_res = client.patch(f"/api/inventory/{variant_id}", json=inv_patch, headers=self.headers_a)
            assert inv_res.status_code == 200, f"Update inventory failed: {inv_res.text}"

            # 4. Place Order via Transactional RPC
            order_payload = {
                "customer_id": customer_id,
                "items": [{"variant_id": variant_id, "quantity": 2}],
                "notes": "Live API integration order",
            }
            ord_res = client.post("/api/orders", json=order_payload, headers=self.headers_a)
            assert ord_res.status_code == 201, f"Create order failed: {ord_res.text}"
            order_data = ord_res.json()
            order_id = order_data["id"]
            assert Decimal(str(order_data["total_amount"])) == Decimal("2500.00")
            assert order_data["status"] == "pending"

            # 5. Order items
            items_res = client.get(f"/api/orders/{order_id}/items", headers=self.headers_a)
            assert items_res.status_code == 200
            items = items_res.json()
            assert len(items) == 1
            assert items[0]["quantity"] == 2

            # 6. Cross-seller isolation: Seller B must NOT be able to view Seller A's order
            b_order_res = client.get(f"/api/orders/{order_id}", headers=self.headers_b)
            assert b_order_res.status_code == 404

            # 7. Fulfill Order
            ful_res = client.post(f"/api/orders/{order_id}/fulfill?target_status=delivered", headers=self.headers_a)
            assert ful_res.status_code == 200, f"Fulfill order failed: {ful_res.text}"
            assert ful_res.json()["status"] == "delivered"

            # 8. Record and Verify Payment
            pay_payload = {
                "order_id": order_id,
                "amount": 2500.00,
                "method": "upi",
                "transaction_reference": f"UPI-{random_suffix}",
            }
            pay_res = client.post("/api/payments", json=pay_payload, headers=self.headers_a)
            assert pay_res.status_code == 201, f"Record payment failed: {pay_res.text}"
            payment_id = pay_res.json()["id"]

            ver_res = client.post(f"/api/payments/{payment_id}/verify", headers=self.headers_a)
            assert ver_res.status_code == 200
            assert ver_res.json()["status"] == "verified"

        finally:
            # Clean up live records in correct dependency order
            sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
            sb.postgrest.auth(self.token_a)

            if payment_id:
                try:
                    sb.table("payments").delete().eq("id", payment_id).execute()
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

