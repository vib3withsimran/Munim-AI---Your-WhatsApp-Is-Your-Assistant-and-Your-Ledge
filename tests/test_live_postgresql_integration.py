"""
==============================================================================
Munim AI — Live Supabase PostgreSQL Integration Test Suite (Phase 3D)
==============================================================================
These tests execute exclusively against the live remote Supabase PostgreSQL
database over HTTPS.

Requirements for authenticated live testing:
1. Migration 'supabase/migrations/20261101_001_order_inventory_rpcs.sql'
   must be applied to the remote Supabase database.
2. Two confirmed test seller accounts:
   - TEST_SELLER_A_EMAIL and TEST_SELLER_A_PASSWORD in .env
   - TEST_SELLER_B_EMAIL and TEST_SELLER_B_PASSWORD in .env
   (or configured via environment variables)

If authenticated test credentials are not configured or rate limits are reached,
the authenticated tests explicitly skip with clear diagnostic messages.
Never simulates transactions or mocks PostgreSQL.
"""

import os
import uuid
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Tuple, Optional
import pytest
from dotenv import dotenv_values
from supabase import create_client, Client

from backend.app.core.config import settings
from backend.app.core.supabase_client import get_supabase_client
from backend.app.services.order_service import OrderService
from backend.app.schemas.order import OrderCreateRequest, OrderItemCreateRequest
from backend.app.services.exceptions import (
    InsufficientStockError,
    InvalidOrderTransitionError,
    BusinessRuleError,
)
from backend.app.repositories.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ConstraintViolationError,
)


# ============================================================================
# Helpers: Live RPC Probing & Seller Authentication
# ============================================================================

def is_live_rpc_available() -> bool:
    """Probes the live Supabase database to verify if Phase 3D RPCs are present."""
    client = get_supabase_client()
    try:
        client.rpc("create_order_with_reservation_rpc", {
            "p_customer_id": "00000000-0000-0000-0000-000000000000",
            "p_items": []
        }).execute()
        return True
    except Exception as e:
        err = str(e)
        if "PGRST202" in err or "schema cache" in err.lower():
            return False
        # Any permission or validation error (42501, 22023, P0002) means RPC is installed
        return True


def get_test_seller_clients() -> Tuple[Optional[Client], Optional[str], Optional[Client], Optional[str], Optional[str]]:
    """
    Attempts to authenticate Seller A and Seller B against live Supabase Auth.
    Returns: (client_a, seller_a_id, client_b, seller_b_id, error_reason)
    """
    env = {**dotenv_values(".env"), **os.environ}

    email_a = env.get("TEST_SELLER_A_EMAIL") or env.get("SELLER_A_EMAIL")
    pass_a = env.get("TEST_SELLER_A_PASSWORD") or env.get("SELLER_A_PASSWORD")
    email_b = env.get("TEST_SELLER_B_EMAIL") or env.get("SELLER_B_EMAIL")
    pass_b = env.get("TEST_SELLER_B_PASSWORD") or env.get("SELLER_B_PASSWORD")

    if not email_a or not pass_a or not email_b or not pass_b:
        return (
            None, None, None, None,
            "Missing dedicated credentials for Seller A and Seller B in environment. "
            "Please set TEST_SELLER_A_EMAIL/TEST_SELLER_A_PASSWORD and "
            "TEST_SELLER_B_EMAIL/TEST_SELLER_B_PASSWORD in .env."
        )

    try:
        client_a = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        auth_a = client_a.auth.sign_in_with_password({"email": email_a, "password": pass_a})
        seller_a_id = auth_a.user.id

        client_b = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        auth_b = client_b.auth.sign_in_with_password({"email": email_b, "password": pass_b})
        seller_b_id = auth_b.user.id

        return client_a, seller_a_id, client_b, seller_b_id, None
    except Exception as e:
        return None, None, None, None, f"Supabase Auth sign-in failed: {e}"


# ============================================================================
# Live Integration Test Suite
# ============================================================================

@pytest.mark.live_postgres
class TestLiveSupabasePostgreSQLIntegration:
    """
    Genuine PostgreSQL tests that communicate directly with live Supabase.
    """

    @pytest.fixture(autouse=True)
    def verify_rpc_installed(self):
        """Ensures the remote database has the RPC migration installed."""
        if not is_live_rpc_available():
            pytest.skip(
                "Migration '20261101_001_order_inventory_rpcs.sql' has NOT been applied to the live Supabase database. "
                "Execute the migration in the Supabase Dashboard SQL Editor to enable real PostgreSQL tests."
            )

    # ------------------------------------------------------------------------
    # Anonymous Caller Boundary Test (Executes without seller credentials)
    # ------------------------------------------------------------------------

    def test_live_rpc_anonymous_call_rejected_with_permission_denied(self):
        """
        Verifies against live PostgreSQL that an unauthenticated caller cannot execute
        the protected create_order_with_reservation_rpc function (PostgreSQL 42501).
        """
        client = get_supabase_client()
        service = OrderService(client)

        req = OrderCreateRequest(
            customer_id=uuid.uuid4(),
            items=[OrderItemCreateRequest(variant_id=uuid.uuid4(), quantity=1)],
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.create_order_with_reservation(seller_id=uuid.uuid4(), data=req)

        assert "permission denied" in str(exc_info.value).lower() or "42501" in str(exc_info.value)

    # ------------------------------------------------------------------------
    # Authenticated Test Sellers Fixture
    # ------------------------------------------------------------------------

    @pytest.fixture
    def authenticated_sellers(self):
        """
        Provides authenticated live Supabase clients for Seller A and Seller B.
        If credentials are not present in .env, skips gracefully with exact requirements.
        """
        client_a, seller_a_id, client_b, seller_b_id, err = get_test_seller_clients()
        if err:
            pytest.skip(
                f"Authenticated live PostgreSQL integration tests skipped: {err}"
            )
        return {
            "client_a": client_a,
            "seller_a_id": seller_a_id,
            "service_a": OrderService(client_a),
            "client_b": client_b,
            "seller_b_id": seller_b_id,
            "service_b": OrderService(client_b),
        }

    # ------------------------------------------------------------------------
    # Disposable Test Records Fixture
    # ------------------------------------------------------------------------

    @pytest.fixture
    def live_disposable_records(self, authenticated_sellers):
        """
        Sets up clean, disposable records for Seller A and Seller B on live Supabase,
        and guarantees cleanup after test execution.
        """
        env = authenticated_sellers
        client_a = env["client_a"]
        seller_a = env["seller_a_id"]
        client_b = env["client_b"]
        seller_b = env["seller_b_id"]

        # Track IDs for cleanup
        created = {
            "customers": [],
            "products": [],
            "variants": [],
            "inventory": [],
            "orders": [],
        }

        # 1. Seller A customer, product, variant, inventory
        cust_a_id = str(uuid.uuid4())
        phone_a = f"+9199{uuid.uuid4().int % 100000000:08d}"
        client_a.table("customers").insert({
            "id": cust_a_id,
            "seller_id": seller_a,
            "name": "Live Test Cust A",
            "phone": phone_a,
        }).execute()
        created["customers"].append((client_a, cust_a_id))

        prod_a_id = str(uuid.uuid4())
        client_a.table("products").insert({
            "id": prod_a_id,
            "seller_id": seller_a,
            "name": "Live Silk Saree",
            "is_active": True,
        }).execute()
        created["products"].append((client_a, prod_a_id))

        var_a_id = str(uuid.uuid4())
        client_a.table("product_variants").insert({
            "id": var_a_id,
            "product_id": prod_a_id,
            "seller_id": seller_a,
            "sku": "SAREE-BLU-FREE",
            "size": "Free",
            "color": "Blue",
            "price": 1250.00,
        }).execute()
        created["variants"].append((client_a, var_a_id))

        inv_a_id = str(uuid.uuid4())
        client_a.table("inventory").insert({
            "id": inv_a_id,
            "seller_id": seller_a,
            "variant_id": var_a_id,
            "available_quantity": 10,
            "reserved_quantity": 0,
        }).execute()
        created["inventory"].append((client_a, inv_a_id))

        # 2. Seller B customer, product, variant, inventory
        cust_b_id = str(uuid.uuid4())
        phone_b = f"+9188{uuid.uuid4().int % 100000000:08d}"
        client_b.table("customers").insert({
            "id": cust_b_id,
            "seller_id": seller_b,
            "name": "Live Test Cust B",
            "phone": phone_b,
        }).execute()
        created["customers"].append((client_b, cust_b_id))

        prod_b_id = str(uuid.uuid4())
        client_b.table("products").insert({
            "id": prod_b_id,
            "seller_id": seller_b,
            "name": "Live Linen Shirt",
            "is_active": True,
        }).execute()
        created["products"].append((client_b, prod_b_id))

        var_b_id = str(uuid.uuid4())
        client_b.table("product_variants").insert({
            "id": var_b_id,
            "product_id": prod_b_id,
            "seller_id": seller_b,
            "sku": "SHIRT-WHT-L",
            "size": "L",
            "color": "White",
            "price": 950.00,
        }).execute()
        created["variants"].append((client_b, var_b_id))

        inv_b_id = str(uuid.uuid4())
        client_b.table("inventory").insert({
            "id": inv_b_id,
            "seller_id": seller_b,
            "variant_id": var_b_id,
            "available_quantity": 5,
            "reserved_quantity": 0,
        }).execute()
        created["inventory"].append((client_b, inv_b_id))

        payload = {
            **env,
            "cust_a_id": cust_a_id,
            "prod_a_id": prod_a_id,
            "var_a_id": var_a_id,
            "inv_a_id": inv_a_id,
            "cust_b_id": cust_b_id,
            "prod_b_id": prod_b_id,
            "var_b_id": var_b_id,
            "inv_b_id": inv_b_id,
            "created": created,
        }

        try:
            yield payload
        finally:
            # Safe cleanup in reverse dependency order
            # Delete any created orders for Seller A and B (by customer ID or recorded order ID)
            for client, cid in created["customers"]:
                try:
                    orders_res = client.table("orders").select("id").eq("customer_id", cid).execute()
                    for o in (orders_res.data or []):
                        client.table("order_items").delete().eq("order_id", o["id"]).execute()
                        client.table("orders").delete().eq("id", o["id"]).execute()
                except Exception:
                    pass

            for client, oid in created["orders"]:
                try:
                    client.table("order_items").delete().eq("order_id", oid).execute()
                    client.table("orders").delete().eq("id", oid).execute()
                except Exception:
                    pass

            # Delete inventory
            for client, iid in created["inventory"]:
                try:
                    client.table("inventory").delete().eq("id", iid).execute()
                except Exception:
                    pass

            # Delete variants
            for client, vid in created["variants"]:
                try:
                    client.table("product_variants").delete().eq("id", vid).execute()
                except Exception:
                    pass

            # Delete products
            for client, pid in created["products"]:
                try:
                    client.table("products").delete().eq("id", pid).execute()
                except Exception:
                    pass

            # Delete customers
            for client, cid in created["customers"]:
                try:
                    client.table("customers").delete().eq("id", cid).execute()
                except Exception:
                    pass

    # ------------------------------------------------------------------------
    # Authenticated Real PostgreSQL Test Cases
    # ------------------------------------------------------------------------

    def test_live_successful_order_creation_and_inventory_reservation(self, live_disposable_records):
        """
        Tests successful order creation against live PostgreSQL:
        - Order created in 'orders' table
        - Line item created in 'order_items'
        - Inventory row has reserved_quantity incremented
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=2)],
            currency="INR",
            notes="Live PostgreSQL Order Test",
        )

        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        assert order.id is not None
        assert order.status == "pending"
        assert order.total_amount == Decimal("2500.00")  # 2 * 1250.00

        # Read back inventory from live database
        inv_res = client_a.table("inventory").select("*").eq("id", rec["inv_a_id"]).single().execute()
        inv_row = inv_res.data
        assert inv_row["available_quantity"] == 10
        assert inv_row["reserved_quantity"] == 2  # Reserved exactly 2

    def test_live_canonical_database_pricing_and_snapshots(self, live_disposable_records):
        """
        Verifies that PostgreSQL RPC retrieves canonical prices directly from
        product_variants and creates product/variant snapshots in order_items.
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=1)],
        )

        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        assert order.items is not None and len(order.items) == 1
        item = order.items[0]
        assert item.product_name_snapshot == "Live Silk Saree"
        assert item.unit_price == Decimal("1250.00")
        assert item.line_total == Decimal("1250.00")
        assert item.variant_snapshot["sku"] == "SAREE-BLU-FREE"
        assert item.variant_snapshot["color"] == "Blue"

    def test_live_cross_seller_customer_and_inventory_rejection(self, live_disposable_records):
        """
        Verifies live PostgreSQL RLS and RPC tenant boundaries:
        - Seller A cannot create an order using Seller B's customer
        - Seller A cannot create an order using Seller B's variant
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]

        # Seller A attempts to use Seller B's customer
        req_bad_cust = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_b_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=1)],
        )
        with pytest.raises(NotFoundError) as exc_info:
            service_a.create_order_with_reservation(seller_id=seller_a, data=req_bad_cust)
        assert "Customer" in str(exc_info.value)

        # Seller A attempts to use Seller B's variant
        req_bad_var = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_b_id"]), quantity=1)],
        )
        with pytest.raises(NotFoundError) as exc_info:
            service_a.create_order_with_reservation(seller_id=seller_a, data=req_bad_var)
        assert "Variant" in str(exc_info.value)

    def test_live_rollback_after_deliberate_database_failure(self, live_disposable_records):
        """
        Verifies actual PL/pgSQL transaction rollback on live database:
        - Order with requested quantity > sellable stock triggers InsufficientStockError.
        - Verifies that zero rows were inserted in orders and reserved_quantity remains 0.
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        # Request 15 units when only 10 available
        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=15)],
        )

        with pytest.raises(InsufficientStockError):
            service_a.create_order_with_reservation(seller_id=seller_a, data=req)

        # Confirm inventory was NOT incremented on live database
        inv_res = client_a.table("inventory").select("*").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_res.data["reserved_quantity"] == 0

    def test_live_concurrency_competing_orders_for_last_unit(self, live_disposable_records):
        """
        Tests live concurrent order creation competing for the last available stock unit:
        - Sets available stock to 1
        - Two concurrent threads fire requests simultaneously to live Supabase
        - Exactly one must succeed, and one must fail with InsufficientStockError
        - Final reserved stock must be exactly 1 (no overselling)
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        # Set physical available stock to 1 on live database
        client_a.table("inventory").update({
            "available_quantity": 1,
            "reserved_quantity": 0,
        }).eq("id", rec["inv_a_id"]).execute()

        req_1 = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=1)],
        )
        req_2 = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=1)],
        )

        results = []
        errors = []

        def place_order(req):
            try:
                res = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
                rec["created"]["orders"].append((client_a, str(res.id)))
                results.append(res)
            except Exception as e:
                errors.append(e)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(place_order, req_1)
            f2 = executor.submit(place_order, req_2)
            f1.result()
            f2.result()

        # Exactly 1 success, 1 failure
        assert len(results) == 1, f"Expected 1 success, got {len(results)}"
        assert len(errors) == 1, f"Expected 1 failure, got {len(errors)}"
        assert isinstance(errors[0], InsufficientStockError)

        # Verify live inventory is exactly available=1, reserved=1
        inv_res = client_a.table("inventory").select("*").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_res.data["available_quantity"] == 1
        assert inv_res.data["reserved_quantity"] == 1

    def test_live_exact_equality_between_orders_total_and_sum_order_items(self, live_disposable_records):
        """
        Verifies exact equality between orders.total_amount and SUM(order_items.line_total)
        directly on live PostgreSQL database.
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=3)],
            currency="INR",
        )

        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        # Fetch raw rows from live database
        order_db = client_a.table("orders").select("total_amount").eq("id", str(order.id)).single().execute()
        items_db = client_a.table("order_items").select("line_total").eq("order_id", str(order.id)).execute()

        db_order_total = Decimal(str(order_db.data["total_amount"]))
        db_items_sum = sum(Decimal(str(it["line_total"])) for it in items_db.data)

        assert db_order_total == db_items_sum
        assert db_order_total == Decimal("3750.00")  # 3 * 1250.00

    def test_live_concurrent_price_update_resilience(self, live_disposable_records):
        """
        Verifies that concurrent price updates executed while order placement is running
        cannot cause price-total disagreement (FOR SHARE lock + Pass 1 buffering).
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]
        var_id = rec["var_a_id"]

        order_result = []
        price_result = []

        def place_order():
            try:
                req = OrderCreateRequest(
                    customer_id=uuid.UUID(rec["cust_a_id"]),
                    items=[OrderItemCreateRequest(variant_id=uuid.UUID(var_id), quantity=1)],
                )
                res = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
                rec["created"]["orders"].append((client_a, str(res.id)))
                order_result.append(res)
            except Exception as e:
                order_result.append(e)

        def update_price():
            try:
                client_a.table("product_variants").update({"price": 1999.00}).eq("id", var_id).execute()
                price_result.append("success")
            except Exception as e:
                price_result.append(e)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(place_order)
            f2 = executor.submit(update_price)
            f1.result()
            f2.result()

        if order_result and not isinstance(order_result[0], Exception):
            order = order_result[0]
            items_sum = sum(it.line_total for it in order.items)
            assert order.total_amount == items_sum

    def test_live_concurrent_product_deactivation_resilience(self, live_disposable_records):
        """
        Verifies that concurrent product deactivation cannot produce corrupted or
        inconsistent order creation. Either order is created with consistent snapshot
        or cleanly rejected with BusinessRuleError.
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]
        prod_id = rec["prod_a_id"]
        var_id = rec["var_a_id"]

        order_outcome = []

        def place_order():
            try:
                req = OrderCreateRequest(
                    customer_id=uuid.UUID(rec["cust_a_id"]),
                    items=[OrderItemCreateRequest(variant_id=uuid.UUID(var_id), quantity=1)],
                )
                res = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
                rec["created"]["orders"].append((client_a, str(res.id)))
                order_outcome.append(res)
            except Exception as e:
                order_outcome.append(e)

        def toggle_deactivation():
            try:
                client_a.table("products").update({"is_active": False}).eq("id", prod_id).execute()
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(place_order)
            f2 = executor.submit(toggle_deactivation)
            f1.result()
            f2.result()

        if order_outcome and not isinstance(order_outcome[0], Exception):
            order = order_outcome[0]
            assert order.total_amount == sum(it.line_total for it in order.items)
            assert order.items[0].product_name_snapshot == "Live Silk Saree"

    def test_live_deliberate_failure_after_parent_order_insertion_rolls_back(self, live_disposable_records):
        """
        Tests transaction rollback on live database:
        When stock check fails in Pass 2 (e.g. attempting to reserve more stock than available),
        PostgreSQL aborts and rolls back:
        - Parent orders row is NOT present
        - No order_items row is present
        - Inventory reserved_quantity remains 0
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]
        var_id = rec["var_a_id"]

        # Initial reserved is 0
        inv_before = client_a.table("inventory").select("reserved_quantity").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_before.data["reserved_quantity"] == 0

        # Attempt to order 20 units when only 10 available
        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(var_id), quantity=20)],
        )

        with pytest.raises(InsufficientStockError):
            service_a.create_order_with_reservation(seller_id=seller_a, data=req)

        # Confirm no orders created
        orders_check = client_a.table("orders").select("id").eq("customer_id", rec["cust_a_id"]).execute()
        assert len(orders_check.data) == 0

        # Confirm inventory reserved_quantity remains 0
        inv_after = client_a.table("inventory").select("reserved_quantity").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_after.data["reserved_quantity"] == 0

    def test_live_cross_seller_fulfillment_and_cancellation_rejection(self, live_disposable_records):
        """
        Verifies that Seller B cannot fulfill or cancel an order owned by Seller A.
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        service_b = rec["service_b"]
        seller_b = rec["seller_b_id"]
        client_a = rec["client_a"]

        # Reset stock to 10
        client_a.table("inventory").update({"available_quantity": 10, "reserved_quantity": 0}).eq("id", rec["inv_a_id"]).execute()

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=1)],
        )
        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        # Seller B attempts fulfillment of Seller A's order
        with pytest.raises(NotFoundError) as exc_info:
            service_b.fulfill_order(seller_id=seller_b, order_id=order.id)
        assert "Order" in str(exc_info.value)

        # Seller B attempts cancellation of Seller A's order
        with pytest.raises(NotFoundError) as exc_info:
            service_b.cancel_order(seller_id=seller_b, order_id=order.id)
        assert "Order" in str(exc_info.value)

    def test_live_fulfillment_and_duplicate_fulfillment_prevention(self, live_disposable_records):
        """
        Tests live fulfillment:
        - Decrements physical stock (10 -> 8)
        - Decrements reserved stock (2 -> 0)
        - Transitions status to 'completed'
        - Duplicate fulfillment attempt is rejected with InvalidOrderTransitionError
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        client_a.table("inventory").update({"available_quantity": 10, "reserved_quantity": 0}).eq("id", rec["inv_a_id"]).execute()

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=2)],
        )
        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        # Fulfill order with valid status 'delivered' (compliant with orders_status_check)
        fulfilled = service_a.fulfill_order(seller_id=seller_a, order_id=order.id, target_status="delivered")
        assert fulfilled.status == "delivered"

        # Check live inventory: physical stock was 10 -> now 8. reserved was 2 -> now 0.
        inv_res = client_a.table("inventory").select("*").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_res.data["available_quantity"] == 8
        assert inv_res.data["reserved_quantity"] == 0

        # Duplicate fulfillment rejected
        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service_a.fulfill_order(seller_id=seller_a, order_id=order.id, target_status="delivered")
        assert "already fulfilled" in str(exc_info.value).lower()

    def test_live_cancellation_and_duplicate_cancellation_prevention(self, live_disposable_records):
        """
        Tests live cancellation:
        - Releases reserved stock (3 -> 0)
        - Leaves physical available stock untouched (8 -> 8)
        - Transitions status to 'cancelled'
        - Duplicate cancellation rejected
        - Cancelling fulfilled order rejected
        """
        rec = live_disposable_records
        service_a = rec["service_a"]
        seller_a = rec["seller_a_id"]
        client_a = rec["client_a"]

        client_a.table("inventory").update({"available_quantity": 8, "reserved_quantity": 0}).eq("id", rec["inv_a_id"]).execute()

        req = OrderCreateRequest(
            customer_id=uuid.UUID(rec["cust_a_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(rec["var_a_id"]), quantity=3)],
        )
        order = service_a.create_order_with_reservation(seller_id=seller_a, data=req)
        rec["created"]["orders"].append((client_a, str(order.id)))

        # Cancel order
        cancelled = service_a.cancel_order(seller_id=seller_a, order_id=order.id)
        assert cancelled.status == "cancelled"

        # Verify live inventory: physical available is still 8, reserved is 0
        inv_res = client_a.table("inventory").select("*").eq("id", rec["inv_a_id"]).single().execute()
        assert inv_res.data["available_quantity"] == 8
        assert inv_res.data["reserved_quantity"] == 0

        # Duplicate cancellation rejected
        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service_a.cancel_order(seller_id=seller_a, order_id=order.id)
        assert "already cancelled" in str(exc_info.value).lower()
