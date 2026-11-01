import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import pytest

from fastapi import status
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from backend.app.main import app
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.services.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
    InvalidOrderTransitionError,
    InvalidPaymentTransitionError,
)
from backend.app.repositories.exceptions import (
    NotFoundError,
    DuplicateRecordError,
    PermissionDeniedError,
    ConstraintViolationError,
)

client = TestClient(app)


# ============================================================================
# In-Memory Stateful PostgREST & RPC Mock Engine
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

    def in_(self, column: str, values: list):
        str_vals = [str(v) for v in values]
        self.rows = [r for r in self.rows if str(r.get(column)) in str_vals]
        return self

    def is_(self, column: str, value: Any):
        if str(value).lower() in ("null", "none"):
            self.rows = [r for r in self.rows if r.get(column) is None]
        else:
            self.rows = [r for r in self.rows if r.get(column) == value]
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

    def delete(self):
        self._action = "delete"
        return self

    def upsert(self, payload: dict, on_conflict: str = None):
        self._action = "upsert"
        self._payload = dict(payload)
        return self

    def execute(self):
        res = MagicMock()
        if self._action == "insert":
            self.store[self.table_name].append(self._payload)
            res.data = [self._payload]
            return res
        elif self._action == "upsert":
            found = False
            for r in self.store[self.table_name]:
                if ("customer_id" in self._payload and str(r.get("customer_id")) == str(self._payload.get("customer_id")) and
                    "seller_id" in self._payload and str(r.get("seller_id")) == str(self._payload.get("seller_id"))):
                    r.update(self._payload)
                    found = True
                    break
            if not found:
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
        elif self._action == "delete":
            deleted_rows = list(self.rows)
            for d in deleted_rows:
                if d in self.store[self.table_name]:
                    self.store[self.table_name].remove(d)
            res.data = deleted_rows
            return res
        else:
            res.data = self.rows
            return res


class MockCompleteDatabase:
    """Combines table CRUD simulation with transactional order RPC simulation."""

    def __init__(self, initial_data: dict = None, authenticated_uid: str = None):
        self.store = initial_data or {
            "customers": [],
            "products": [],
            "product_variants": [],
            "inventory": [],
            "orders": [],
            "order_items": [],
            "payments": [],
            "privacy_settings": [],
        }
        self.authenticated_uid = authenticated_uid
        self.postgrest = MagicMock()
        self.auth = MagicMock()

    def table(self, name: str):
        if name not in self.store:
            self.store[name] = []
        return MockQuery(name, self.store)

    def rpc(self, func_name: str, params: Dict[str, Any]):
        class ExecutableRPC:
            def __init__(self, db: MockCompleteDatabase, name: str, args: Dict[str, Any]):
                self.db = db
                self.name = name
                self.args = args

            def execute(self):
                mock_res = MagicMock()
                if self.name == "create_order_with_reservation_rpc":
                    mock_res.data = [self.db._exec_create_order_rpc(self.args)]
                    return mock_res
                elif self.name == "fulfill_order_rpc":
                    mock_res.data = [self.db._exec_fulfill_order_rpc(self.args)]
                    return mock_res
                elif self.name == "cancel_order_rpc":
                    mock_res.data = [self.db._exec_cancel_order_rpc(self.args)]
                    return mock_res
                raise RuntimeError(f"Unknown RPC: {self.name}")

        return ExecutableRPC(self, func_name, params)

    def _exec_create_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = str(params.get("p_seller_id") or self.authenticated_uid)
        customer_id = str(params["p_customer_id"])
        items = params.get("p_items") or []

        # Customer check
        cust = next((c for c in self.store["customers"] if str(c.get("id")) == customer_id and str(c.get("seller_id")) == seller_id), None)
        if not cust:
            raise Exception(f"NOT_FOUND: Customer {customer_id} not found or not owned by seller")

        if not items:
            raise Exception("INVALID_INPUT: Order items must be non-empty")

        total_amount = Decimal("0.00")
        line_specs = []
        order_id = str(uuid.uuid4())

        for it in items:
            vid = str(it["variant_id"])
            qty = it["quantity"]
            if qty <= 0:
                raise Exception("INVALID_QUANTITY: Quantity must be positive")

            var = next((v for v in self.store["product_variants"] if str(v.get("id")) == vid and str(v.get("seller_id")) == seller_id), None)
            if not var:
                raise Exception(f"NOT_FOUND: Variant {vid} not found")

            prod = next((p for p in self.store["products"] if str(p.get("id")) == str(var["product_id"])), None)
            if not prod or not prod.get("is_active", True):
                raise Exception(f"INACTIVE_PRODUCT: Product {prod.get('name') if prod else ''} is inactive")

            inv = next((i for i in self.store["inventory"] if str(i.get("variant_id")) == vid and str(i.get("seller_id")) == seller_id), None)
            if not inv:
                raise Exception(f"NOT_FOUND: Inventory for variant {vid} not found")

            sellable = inv["available_quantity"] - inv["reserved_quantity"]
            if sellable < qty:
                raise Exception(f"INSUFFICIENT_STOCK: Insufficient stock for variant {vid}. Sellable: {sellable}, requested: {qty}")

            unit_price = Decimal(str(var["price"]))
            line_total = round(unit_price * Decimal(qty), 2)
            total_amount += line_total

            line_specs.append({
                "variant_id": vid,
                "quantity": qty,
                "unit_price": unit_price,
                "line_total": line_total,
                "product_name": prod["name"],
                "variant_snapshot": {"sku": var.get("sku"), "size": var.get("size"), "color": var.get("color")},
                "inv_ref": inv,
            })

        # Insert parent order
        order_record = {
            "id": order_id,
            "seller_id": seller_id,
            "customer_id": customer_id,
            "status": "pending",
            "total_amount": total_amount,
            "currency": params.get("p_currency", "INR"),
            "notes": params.get("p_notes"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store["orders"].append(order_record)

        # Mutate inventory & insert items
        for spec in line_specs:
            spec["inv_ref"]["reserved_quantity"] += spec["quantity"]
            item_record = {
                "id": str(uuid.uuid4()),
                "order_id": order_id,
                "seller_id": seller_id,
                "variant_id": spec["variant_id"],
                "quantity": spec["quantity"],
                "unit_price": spec["unit_price"],
                "line_total": spec["line_total"],
                "product_name_snapshot": spec["product_name"],
                "variant_snapshot": spec["variant_snapshot"],
            }
            self.store["order_items"].append(item_record)

        return order_record

    def _exec_fulfill_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = str(params.get("p_seller_id") or self.authenticated_uid)
        order_id = str(params["p_order_id"])
        target_status = params.get("p_target_status", "delivered")

        order = next((o for o in self.store["orders"] if str(o.get("id")) == order_id and str(o.get("seller_id")) == seller_id), None)
        if not order:
            raise Exception(f"NOT_FOUND: Order {order_id} not found")

        curr_status = str(order["status"]).lower()
        if curr_status in ("delivered", "completed"):
            raise Exception("INVALID_ORDER_TRANSITION: Order already fulfilled")
        if curr_status == "cancelled":
            raise Exception("INVALID_ORDER_TRANSITION: Order is cancelled")

        # Items
        items = [it for it in self.store["order_items"] if str(it.get("order_id")) == order_id]
        for it in items:
            vid = str(it["variant_id"])
            qty = it["quantity"]
            inv = next((i for i in self.store["inventory"] if str(i.get("variant_id")) == vid and str(i.get("seller_id")) == seller_id), None)
            if inv:
                inv["available_quantity"] -= qty
                inv["reserved_quantity"] -= qty

        order["status"] = target_status
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        return order

    def _exec_cancel_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = str(params.get("p_seller_id") or self.authenticated_uid)
        order_id = str(params["p_order_id"])

        order = next((o for o in self.store["orders"] if str(o.get("id")) == order_id and str(o.get("seller_id")) == seller_id), None)
        if not order:
            raise Exception(f"NOT_FOUND: Order {order_id} not found")

        curr_status = str(order["status"]).lower()
        if curr_status in ("delivered", "completed"):
            raise Exception("INVALID_ORDER_TRANSITION: Order already fulfilled")
        if curr_status == "cancelled":
            raise Exception("INVALID_ORDER_TRANSITION: Order already cancelled")

        items = [it for it in self.store["order_items"] if str(it.get("order_id")) == order_id]
        for it in items:
            vid = str(it["variant_id"])
            qty = it["quantity"]
            inv = next((i for i in self.store["inventory"] if str(i.get("variant_id")) == vid and str(i.get("seller_id")) == seller_id), None)
            if inv:
                inv["reserved_quantity"] -= qty

        order["status"] = "cancelled"
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        return order


# ============================================================================
# Fixtures
# ============================================================================

SELLER_1_ID = "11111111-1111-1111-1111-111111111111"
SELLER_2_ID = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def mock_db():
    return MockCompleteDatabase(authenticated_uid=SELLER_1_ID)


@pytest.fixture
def auth_seller_1(mock_db):
    seller = AuthenticatedSeller(id=SELLER_1_ID, db=mock_db)
    app.dependency_overrides[get_current_seller] = lambda: seller
    yield seller
    app.dependency_overrides.pop(get_current_seller, None)


# ============================================================================
# 1. Authentication Enforcement Tests
# ============================================================================

class TestAuthenticationEnforcement:
    def test_unauthenticated_requests_return_401(self):
        """All protected routes reject unauthenticated requests with HTTP 401."""
        app.dependency_overrides.pop(get_current_seller, None)

        endpoints = [
            ("GET", "/api/customers"),
            ("POST", "/api/customers"),
            ("GET", "/api/products"),
            ("POST", "/api/products"),
            ("GET", "/api/inventory"),
            ("GET", "/api/orders"),
            ("POST", "/api/orders"),
            ("GET", "/api/payments"),
            ("POST", "/api/payments"),
            ("GET", "/api/dashboard/summary"),
        ]

        for method, url in endpoints:
            if method == "GET":
                res = client.get(url)
            else:
                res = client.post(url, json={})
            assert res.status_code == status.HTTP_401_UNAUTHORIZED, f"Failed on {method} {url}"
            assert "authentication required" in res.json()["detail"].lower()

    def test_invalid_bearer_token_returns_401(self):
        """Invalid or expired Bearer token returns HTTP 401."""
        app.dependency_overrides.pop(get_current_seller, None)
        with patch("backend.app.core.auth.get_supabase_client") as mock_auth_client:
            mock_client = MagicMock()
            mock_client.auth.get_user.side_effect = AuthApiError(message="Invalid token", status=401, code="invalid_token")
            mock_auth_client.return_value = mock_client

            res = client.get("/api/customers", headers={"Authorization": "Bearer bad_token"})
            assert res.status_code == status.HTTP_401_UNAUTHORIZED
            assert "invalid or expired" in res.json()["detail"].lower()


# ============================================================================
# 2. Customer Endpoints Tests
# ============================================================================

class TestCustomerEndpoints:
    def test_create_and_get_customer(self, auth_seller_1):
        """POST /api/customers creates customer; GET /api/customers/{id} retrieves it."""
        payload = {
            "phone": "+91 98765 43210",
            "name": "Priya Sharma",
            "notes": "Prefers WhatsApp updates",
        }
        res = client.post("/api/customers", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["phone"] == "+919876543210"
        assert data["name"] == "Priya Sharma"
        assert data["seller_id"] == SELLER_1_ID
        cust_id = data["id"]

        # GET by ID
        get_res = client.get(f"/api/customers/{cust_id}", headers={"Authorization": "Bearer dummy"})
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()["name"] == "Priya Sharma"

    def test_create_customer_duplicate_phone_rejected(self, auth_seller_1):
        """Creating customer with existing phone returns 409 Conflict."""
        payload = {"phone": "9876543210", "name": "Buyer 1"}
        res1 = client.post("/api/customers", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res1.status_code == status.HTTP_201_CREATED

        # Duplicate
        res2 = client.post("/api/customers", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res2.status_code == status.HTTP_409_CONFLICT

    def test_create_customer_invalid_phone_rejected(self, auth_seller_1):
        """Invalid phone string returns 422 Unprocessable Entity."""
        payload = {"phone": "123", "name": "Too Short"}
        res = client.post("/api/customers", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_customers_pagination(self, auth_seller_1):
        """GET /api/customers supports limit and offset."""
        for i in range(5):
            client.post("/api/customers", json={"phone": f"987654321{i}", "name": f"Buyer {i}"}, headers={"Authorization": "Bearer dummy"})

        res = client.get("/api/customers?limit=2&offset=1", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        assert len(res.json()) == 2

    def test_update_and_delete_customer(self, auth_seller_1):
        """PATCH /api/customers/{id} updates notes; DELETE archives customer."""
        res = client.post("/api/customers", json={"phone": "9876500000", "name": "Temp Customer"}, headers={"Authorization": "Bearer dummy"})
        cust_id = res.json()["id"]

        # PATCH
        patch_res = client.patch(f"/api/customers/{cust_id}", json={"notes": "VIP Client"}, headers={"Authorization": "Bearer dummy"})
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()["notes"] == "VIP Client"

        # DELETE
        del_res = client.delete(f"/api/customers/{cust_id}", headers={"Authorization": "Bearer dummy"})
        assert del_res.status_code == status.HTTP_200_OK
        assert del_res.json()["success"] is True

    def test_customer_cross_seller_isolation(self, mock_db):
        """Seller 2 cannot access Seller 1's customer."""
        # Insert customer for Seller 1
        mock_db.store["customers"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "phone": "9999999999",
            "name": "Secret Client",
            "notes": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        cust_id = mock_db.store["customers"][-1]["id"]

        # Authenticate as Seller 2
        seller_2 = AuthenticatedSeller(id=SELLER_2_ID, db=mock_db)
        app.dependency_overrides[get_current_seller] = lambda: seller_2

        get_res = client.get(f"/api/customers/{cust_id}", headers={"Authorization": "Bearer dummy"})
        assert get_res.status_code == status.HTTP_404_NOT_FOUND

        patch_res = client.patch(f"/api/customers/{cust_id}", json={"name": "Hacked"}, headers={"Authorization": "Bearer dummy"})
        assert patch_res.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# 3. Product & Variant Endpoints Tests
# ============================================================================

class TestProductEndpoints:
    def test_create_and_get_product(self, auth_seller_1):
        """POST /api/products creates product; GET /api/products/{id} retrieves it."""
        payload = {
            "name": "Silk Embroidered Anarkali",
            "description": "Pure festive silk",
            "category": "Ethnic Wear",
            "is_active": True,
        }
        res = client.post("/api/products", json=payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        pdata = res.json()
        assert pdata["name"] == "Silk Embroidered Anarkali"
        assert pdata["seller_id"] == SELLER_1_ID
        prod_id = pdata["id"]

        # GET
        get_res = client.get(f"/api/products/{prod_id}", headers={"Authorization": "Bearer dummy"})
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()["name"] == "Silk Embroidered Anarkali"

    def test_create_product_empty_name_rejected(self, auth_seller_1):
        """Empty product name returns 422."""
        res = client.post("/api/products", json={"name": "   "}, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_and_archive_product(self, auth_seller_1):
        """PATCH updates fields; DELETE archives product."""
        res = client.post("/api/products", json={"name": "Cotton Kurti"}, headers={"Authorization": "Bearer dummy"})
        prod_id = res.json()["id"]

        # PATCH
        patch_res = client.patch(f"/api/products/{prod_id}", json={"category": "Daily Wear"}, headers={"Authorization": "Bearer dummy"})
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()["category"] == "Daily Wear"

        # DELETE (Archive)
        del_res = client.delete(f"/api/products/{prod_id}", headers={"Authorization": "Bearer dummy"})
        assert del_res.status_code == status.HTTP_200_OK

        # Verify is_active=False
        get_res = client.get(f"/api/products/{prod_id}", headers={"Authorization": "Bearer dummy"})
        assert get_res.json()["is_active"] is False

    def test_create_and_list_variants(self, auth_seller_1):
        """POST /api/products/{id}/variants creates variant; GET /api/products/{id}/variants lists them."""
        pres = client.post("/api/products", json={"name": "Designer Saree"}, headers={"Authorization": "Bearer dummy"})
        prod_id = pres.json()["id"]

        # Create Variant
        vres = client.post(
            f"/api/products/{prod_id}/variants",
            json={"sku": "SAR-RED-FREE", "color": "Red", "price": 1499.00},
            headers={"Authorization": "Bearer dummy"},
        )
        assert vres.status_code == status.HTTP_201_CREATED
        vdata = vres.json()
        assert vdata["sku"] == "SAR-RED-FREE"
        assert vdata["product_id"] == prod_id
        assert Decimal(str(vdata["price"])) == Decimal("1499.00")

        # List Variants
        list_res = client.get(f"/api/products/{prod_id}/variants", headers={"Authorization": "Bearer dummy"})
        assert list_res.status_code == status.HTTP_200_OK
        assert len(list_res.json()) == 1
        assert list_res.json()[0]["sku"] == "SAR-RED-FREE"

    def test_create_variant_mismatched_product_id_rejected(self, auth_seller_1):
        """Mismatched product_id in body vs URL returns 400."""
        pres = client.post("/api/products", json={"name": "Pants"}, headers={"Authorization": "Bearer dummy"})
        prod_id = pres.json()["id"]

        other_id = str(uuid.uuid4())
        vres = client.post(
            f"/api/products/{prod_id}/variants",
            json={"product_id": other_id, "sku": "PNT-M", "price": 499.00},
            headers={"Authorization": "Bearer dummy"},
        )
        assert vres.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_variant_negative_price_rejected(self, auth_seller_1):
        """Negative variant price returns 422."""
        pres = client.post("/api/products", json={"name": "Shirt"}, headers={"Authorization": "Bearer dummy"})
        prod_id = pres.json()["id"]

        vres = client.post(
            f"/api/products/{prod_id}/variants",
            json={"price": -100.00},
            headers={"Authorization": "Bearer dummy"},
        )
        assert vres.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# 4. Inventory Endpoints Tests
# ============================================================================

class TestInventoryEndpoints:
    def test_get_and_update_inventory(self, auth_seller_1, mock_db):
        """GET /api/inventory/{variant_id} retrieves inventory; PATCH updates stock."""
        vid = str(uuid.uuid4())
        pid = str(uuid.uuid4())

        # Seed variant & inventory
        mock_db.store["products"].append({"id": pid, "seller_id": SELLER_1_ID, "name": "Item", "is_active": True})
        mock_db.store["product_variants"].append({"id": vid, "product_id": pid, "seller_id": SELLER_1_ID, "price": 500.0})
        mock_db.store["inventory"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "variant_id": vid,
            "available_quantity": 20,
            "reserved_quantity": 5,
            "low_stock_threshold": 3,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        # GET
        res = client.get(f"/api/inventory/{vid}", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["available_quantity"] == 20
        assert res.json()["reserved_quantity"] == 5

        # PATCH
        patch_res = client.patch(
            f"/api/inventory/{vid}",
            json={"available_quantity": 25, "low_stock_threshold": 5},
            headers={"Authorization": "Bearer dummy"},
        )
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()["available_quantity"] == 25
        assert patch_res.json()["low_stock_threshold"] == 5

    def test_update_inventory_reserved_exceeds_available_rejected(self, auth_seller_1, mock_db):
        """Reserved stock cannot exceed physical available stock (400 Bad Request)."""
        vid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        mock_db.store["products"].append({"id": pid, "seller_id": SELLER_1_ID, "name": "Item", "is_active": True})
        mock_db.store["product_variants"].append({"id": vid, "product_id": pid, "seller_id": SELLER_1_ID, "price": 500.0})
        mock_db.store["inventory"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "variant_id": vid,
            "available_quantity": 10,
            "reserved_quantity": 2,
            "low_stock_threshold": 2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        res = client.patch(
            f"/api/inventory/{vid}",
            json={"reserved_quantity": 15},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_inventory_low_stock_filter(self, auth_seller_1, mock_db):
        """GET /api/inventory?low_stock_only=true filters low stock items."""
        mock_db.store["inventory"].extend([
            {"id": str(uuid.uuid4()), "seller_id": SELLER_1_ID, "variant_id": str(uuid.uuid4()), "available_quantity": 10, "reserved_quantity": 0, "low_stock_threshold": 2, "updated_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "seller_id": SELLER_1_ID, "variant_id": str(uuid.uuid4()), "available_quantity": 1, "reserved_quantity": 0, "low_stock_threshold": 3, "updated_at": datetime.now(timezone.utc).isoformat()},
        ])

        res = client.get("/api/inventory?low_stock_only=true", headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert len(data) == 1
        assert data[0]["available_quantity"] == 1


# ============================================================================
# 5. Order Endpoints Tests (Transactional RPC Integration)
# ============================================================================

class TestOrderEndpoints:
    def test_create_order_authoritative_pricing_and_reservation(self, auth_seller_1, mock_db):
        """
        POST /api/orders uses PostgreSQL transactional RPC:
        - Total is strictly server-authoritative.
        - Physical stock is reserved.
        """
        # Setup customer, product, variant, inventory
        cid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        vid = str(uuid.uuid4())

        mock_db.store["customers"].append({"id": cid, "seller_id": SELLER_1_ID, "phone": "9876543210", "name": "Buyer"})
        mock_db.store["products"].append({"id": pid, "seller_id": SELLER_1_ID, "name": "Festive Kurta", "is_active": True})
        mock_db.store["product_variants"].append({"id": vid, "product_id": pid, "seller_id": SELLER_1_ID, "price": 950.00, "sku": "KUR-L"})
        mock_db.store["inventory"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "variant_id": vid,
            "available_quantity": 10,
            "reserved_quantity": 0,
            "low_stock_threshold": 2,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        order_payload = {
            "customer_id": cid,
            "items": [{"variant_id": vid, "quantity": 2}],
            "notes": "Fast delivery requested",
        }

        res = client.post("/api/orders", json=order_payload, headers={"Authorization": "Bearer dummy"})
        assert res.status_code == status.HTTP_201_CREATED
        odata = res.json()
        assert Decimal(str(odata["total_amount"])) == Decimal("1900.00")  # 950.00 * 2
        assert odata["status"] == "pending"
        order_id = odata["id"]

        # Verify inventory reserved
        inv = next(i for i in mock_db.store["inventory"] if str(i["variant_id"]) == vid)
        assert inv["reserved_quantity"] == 2

        # Verify order items
        items_res = client.get(f"/api/orders/{order_id}/items", headers={"Authorization": "Bearer dummy"})
        assert items_res.status_code == status.HTTP_200_OK
        items_data = items_res.json()
        assert len(items_data) == 1
        assert items_data[0]["product_name_snapshot"] == "Festive Kurta"
        assert Decimal(str(items_data[0]["line_total"])) == Decimal("1900.00")

    def test_create_order_insufficient_stock_fails(self, auth_seller_1, mock_db):
        """Ordering more than sellable stock returns 400 Bad Request."""
        cid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        vid = str(uuid.uuid4())
        mock_db.store["customers"].append({"id": cid, "seller_id": SELLER_1_ID, "phone": "9876543210"})
        mock_db.store["products"].append({"id": pid, "seller_id": SELLER_1_ID, "name": "Item", "is_active": True})
        mock_db.store["product_variants"].append({"id": vid, "product_id": pid, "seller_id": SELLER_1_ID, "price": 100.0})
        mock_db.store["inventory"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "variant_id": vid,
            "available_quantity": 2,
            "reserved_quantity": 1,  # Only 1 sellable
            "low_stock_threshold": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        res = client.post(
            "/api/orders",
            json={"customer_id": cid, "items": [{"variant_id": vid, "quantity": 5}]},
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_fulfill_and_cancel_order(self, auth_seller_1, mock_db):
        """POST /api/orders/{id}/fulfill and POST /api/orders/{id}/cancel."""
        cid = str(uuid.uuid4())
        pid = str(uuid.uuid4())
        vid = str(uuid.uuid4())
        mock_db.store["customers"].append({"id": cid, "seller_id": SELLER_1_ID, "phone": "9876543210"})
        mock_db.store["products"].append({"id": pid, "seller_id": SELLER_1_ID, "name": "Item", "is_active": True})
        mock_db.store["product_variants"].append({"id": vid, "product_id": pid, "seller_id": SELLER_1_ID, "price": 100.0})
        mock_db.store["inventory"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_1_ID,
            "variant_id": vid,
            "available_quantity": 10,
            "reserved_quantity": 0,
            "low_stock_threshold": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        # Create Order
        res = client.post(
            "/api/orders",
            json={"customer_id": cid, "items": [{"variant_id": vid, "quantity": 3}]},
            headers={"Authorization": "Bearer dummy"},
        )
        oid = res.json()["id"]

        # Fulfill
        fres = client.post(f"/api/orders/{oid}/fulfill?target_status=delivered", headers={"Authorization": "Bearer dummy"})
        assert fres.status_code == status.HTTP_200_OK
        assert fres.json()["status"] == "delivered"

        # Check inventory: physical decremented, reserved released
        inv = next(i for i in mock_db.store["inventory"] if str(i["variant_id"]) == vid)
        assert inv["available_quantity"] == 7
        assert inv["reserved_quantity"] == 0

        # Duplicate fulfillment rejected
        dup_res = client.post(f"/api/orders/{oid}/fulfill", headers={"Authorization": "Bearer dummy"})
        assert dup_res.status_code == status.HTTP_400_BAD_REQUEST

        # Cancel on fulfilled order rejected
        can_res = client.post(f"/api/orders/{oid}/cancel", headers={"Authorization": "Bearer dummy"})
        assert can_res.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# 6. Payment Endpoints Tests
# ============================================================================

class TestPaymentEndpoints:
    def test_record_and_verify_payment(self, auth_seller_1, mock_db):
        """POST /api/payments records payment; POST /api/payments/{id}/verify verifies it."""
        oid = str(uuid.uuid4())
        mock_db.store["orders"].append({
            "id": oid,
            "seller_id": SELLER_1_ID,
            "customer_id": str(uuid.uuid4()),
            "status": "pending",
            "total_amount": Decimal("1500.00"),
            "currency": "INR",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Record payment
        res = client.post(
            "/api/payments",
            json={
                "order_id": oid,
                "amount": 1500.00,
                "method": "upi",
                "transaction_reference": "UPI987654321",
            },
            headers={"Authorization": "Bearer dummy"},
        )
        assert res.status_code == status.HTTP_201_CREATED
        pdata = res.json()
        assert pdata["status"] == "pending"
        pay_id = pdata["id"]

        # Verify payment
        v_res = client.post(f"/api/payments/{pay_id}/verify", headers={"Authorization": "Bearer dummy"})
        assert v_res.status_code == status.HTTP_200_OK
        assert v_res.json()["status"] == "verified"
        assert v_res.json()["paid_at"] is not None

    def test_reject_payment(self, auth_seller_1, mock_db):
        """POST /api/payments/{id}/reject marks payment rejected."""
        oid = str(uuid.uuid4())
        mock_db.store["orders"].append({"id": oid, "seller_id": SELLER_1_ID, "total_amount": 500.0})

        res = client.post(
            "/api/payments",
            json={"order_id": oid, "amount": 500.00, "method": "cash"},
            headers={"Authorization": "Bearer dummy"},
        )
        pay_id = res.json()["id"]

        rej_res = client.post(f"/api/payments/{pay_id}/reject", headers={"Authorization": "Bearer dummy"})
        assert rej_res.status_code == status.HTTP_200_OK
        assert rej_res.json()["status"] == "rejected"

    def test_payment_cross_seller_isolation(self, mock_db):
        """Seller 2 cannot verify or access Seller 1's payment."""
        pay_id = str(uuid.uuid4())
        mock_db.store["payments"].append({
            "id": pay_id,
            "seller_id": SELLER_1_ID,
            "order_id": str(uuid.uuid4()),
            "amount": Decimal("500.00"),
            "method": "upi",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        # Authenticate as Seller 2
        seller_2 = AuthenticatedSeller(id=SELLER_2_ID, db=mock_db)
        app.dependency_overrides[get_current_seller] = lambda: seller_2

        get_res = client.get(f"/api/payments/{pay_id}", headers={"Authorization": "Bearer dummy"})
        assert get_res.status_code == status.HTTP_404_NOT_FOUND

        v_res = client.post(f"/api/payments/{pay_id}/verify", headers={"Authorization": "Bearer dummy"})
        assert v_res.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# 7. Dashboard Endpoints Tests
# ============================================================================

class TestDashboardEndpoints:
    def test_dashboard_routes_accessible(self, auth_seller_1):
        """Both /dashboard/... and /api/dashboard/... routes work correctly."""
        from backend.app.models.dashboard_schemas import (
            DashboardSummaryResponse,
            StatMetric,
            StatCardItem,
        )

        mock_response = DashboardSummaryResponse(
            revenue=StatMetric(value=15000.0, formatted="₹15,000", change=5.0),
            orders=StatMetric(value=12.0, formatted="12", change=2.0),
            active_customers=StatMetric(value=8.0, formatted="8", change=1.0),
            pending_dues=StatMetric(value=2500.0, formatted="₹2,500", change=0.0),
            stats=[
                StatCardItem(icon="IndianRupee", label="Monthly Revenue", value="₹15,000", numeric_value=15000.0),
                StatCardItem(icon="Package", label="Total Orders", value="12", numeric_value=12.0),
                StatCardItem(icon="Users", label="Active Customers", value="8", numeric_value=8.0),
                StatCardItem(icon="Clock", label="Pending Dues", value="₹2,500", numeric_value=2500.0),
            ],
        )

        with patch("backend.app.api.routes.dashboard.get_dashboard_summary", return_value=mock_response):
            res1 = client.get("/dashboard/summary", headers={"Authorization": "Bearer dummy"})
            assert res1.status_code == status.HTTP_200_OK

            res2 = client.get("/api/dashboard/summary", headers={"Authorization": "Bearer dummy"})
            assert res2.status_code == status.HTTP_200_OK
            assert res2.json()["orders"]["value"] == 12.0
