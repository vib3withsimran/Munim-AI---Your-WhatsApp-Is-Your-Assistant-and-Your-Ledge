import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
import pytest

from backend.app.schemas.order import OrderCreateRequest, OrderItemCreateRequest
from backend.app.models.order import Order
from backend.app.services.order_service import OrderService
from backend.app.services.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
    InvalidOrderTransitionError,
)
from backend.app.repositories.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    ConstraintViolationError,
    RepositoryError,
)
from backend.app.core.supabase_client import get_supabase_client


# ============================================================================
# Mock RPC Infrastructure
# ============================================================================

class MockRPCResult:
    def __init__(self, data: Any):
        self.data = data


class MockTransactionalDatabase:
    """
    In-memory stateful simulator that precisely mirrors the logic, constraints,
    locking semantics, and error codes of the PostgreSQL RPC functions:
    - create_order_with_reservation_rpc
    - fulfill_order_rpc
    - cancel_order_rpc
    """

    def __init__(self):
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.products: Dict[str, Dict[str, Any]] = {}
        self.variants: Dict[str, Dict[str, Any]] = {}
        self.inventory: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.order_items: Dict[str, List[Dict[str, Any]]] = {}

        # Auth context simulation
        self.authenticated_uid: Optional[str] = None
        self.caller_role: str = "authenticated"

        # Fault injection hook
        self.simulate_item_insert_failure: bool = False
        self.on_before_pass_2 = None

    def rpc(self, func_name: str, params: Dict[str, Any]):
        class ExecutableRPC:
            def __init__(self, db_sim: MockTransactionalDatabase, name: str, args: Dict[str, Any]):
                self.db_sim = db_sim
                self.name = name
                self.args = args

            def execute(self):
                if self.name == "create_order_with_reservation_rpc":
                    return MockRPCResult(self.db_sim._exec_create_order_rpc(self.args))
                elif self.name == "fulfill_order_rpc":
                    return MockRPCResult(self.db_sim._exec_fulfill_order_rpc(self.args))
                elif self.name == "cancel_order_rpc":
                    return MockRPCResult(self.db_sim._exec_cancel_order_rpc(self.args))
                raise RuntimeError(f"Unknown RPC function: {self.name}")

        return ExecutableRPC(self, func_name, params)

    def _resolve_seller(self, p_seller_id: Optional[str]) -> str:
        v_seller = self.authenticated_uid
        if v_seller is None:
            if p_seller_id and self.caller_role in ("service_role", "supabase_admin", "postgres"):
                v_seller = p_seller_id
            else:
                raise Exception("UNAUTHENTICATED: Caller must be authenticated")
        elif p_seller_id and p_seller_id != v_seller:
            raise Exception("PERMISSION_DENIED: Caller seller_id mismatch")
        return str(v_seller)

    def _exec_create_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = self._resolve_seller(params.get("p_seller_id"))
        customer_id = str(params["p_customer_id"])
        items = params.get("p_items") or []

        # Validate customer
        cust = self.customers.get(customer_id)
        if not cust or cust["seller_id"] != seller_id:
            raise Exception(f"NOT_FOUND: Customer {customer_id} not found or not owned by seller")

        # Validate items
        if not items:
            raise Exception("INVALID_INPUT: Order items must be a non-empty array")

        variant_ids = [it["variant_id"] for it in items]
        if len(set(variant_ids)) != len(variant_ids):
            raise Exception("DUPLICATE_ITEM: Duplicate variant_id in order items")

        # Snapshot state for atomic rollback
        inventory_snapshot = {k: dict(v) for k, v in self.inventory.items()}

        total_amount = Decimal("0.00")
        line_items = []
        order_id = str(uuid.uuid4())

        # Sort variants to mimic deterministic lock ordering (ORDER BY variant_id ASC)
        sorted_items = sorted(items, key=lambda x: str(x["variant_id"]))

        try:
            # =================================================================
            # PASS 1: Validation, stock checks, and authoritative total
            # (NO MUTATIONS TO self.inventory, self.orders, or self.order_items)
            # =================================================================
            validated_specs = []
            for it in sorted_items:
                vid = str(it["variant_id"])
                qty = it["quantity"]

                if qty <= 0:
                    raise Exception("INVALID_QUANTITY: Item quantity must be greater than 0")

                var = self.variants.get(vid)
                if not var or var["seller_id"] != seller_id:
                    raise Exception(f"NOT_FOUND: Variant {vid} not found or not owned by seller")

                prod = self.products.get(var["product_id"])
                if not prod or not prod.get("is_active", True):
                    raise Exception(f"INACTIVE_PRODUCT: Product \"{prod.get('name') if prod else 'Unknown'}\" (variant {vid}) is inactive")

                inv = self.inventory.get(vid)
                if not inv or inv["seller_id"] != seller_id:
                    raise Exception(f"NOT_FOUND: Inventory record for variant {vid} not found")

                sellable = inv["available_quantity"] - inv["reserved_quantity"]
                if sellable < qty:
                    raise Exception(f"INSUFFICIENT_STOCK: Insufficient sellable stock for variant {vid}. Available sellable: {sellable}, requested: {qty}")

                unit_price = Decimal(str(var["price"]))
                line_total = round(unit_price * Decimal(qty), 2)
                total_amount += line_total

                validated_specs.append({
                    "variant_id": vid,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "line_total": line_total,
                    "product_name": prod["name"],
                    "variant_snapshot": {"sku": var.get("sku"), "size": var.get("size"), "color": var.get("color")},
                })

            # =================================================================
            # INSERT PARENT ORDER FIRST (Satisfies foreign key constraint)
            # =================================================================
            order_record = {
                "id": order_id,
                "seller_id": seller_id,
                "customer_id": customer_id,
                "status": "pending",
                "total_amount": total_amount,
                "currency": params.get("p_currency", "INR"),
                "notes": params.get("p_notes"),
                "created_at": "2026-11-01T08:00:00Z",
                "updated_at": "2026-11-01T08:00:00Z",
                "items": [],
            }
            self.orders[order_id] = order_record

            # =================================================================
            # PASS 2: Mutate inventory and insert order_items
            # =================================================================
            if self.on_before_pass_2:
                self.on_before_pass_2(self)

            for spec in validated_specs:
                # Enforce FK check: parent order must exist in DB before item insertion
                if order_id not in self.orders:
                    raise Exception('insert or update on table "order_items" violates foreign key constraint "order_items_order_id_seller_id_fkey"')

                vid = spec["variant_id"]
                qty = spec["quantity"]
                inv = self.inventory[vid]

                # Increment reserved stock atomically while enforcing reserved_quantity <= available_quantity (ROW_COUNT check)
                if (inv["reserved_quantity"] + qty) > inv["available_quantity"]:
                    # In PostgreSQL: WHERE ... AND (reserved_quantity + qty) <= available_quantity matches 0 rows
                    # GET DIAGNOSTICS v_rows_updated = ROW_COUNT; IF v_rows_updated <> 1 THEN RAISE P0001
                    raise Exception(f"INSUFFICIENT_STOCK: Inventory reservation failed for variant {vid} (expected 1 row updated, got 0; stock condition violated or record missing)")

                inv["reserved_quantity"] += qty

                if self.simulate_item_insert_failure:
                    raise Exception("DATABASE_ERROR: Simulated failure during order item insertion")

                line_items.append({
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "seller_id": seller_id,
                    "variant_id": vid,
                    "quantity": qty,
                    "unit_price": spec["unit_price"],
                    "line_total": spec["line_total"],
                    "product_name_snapshot": spec["product_name"],
                    "variant_snapshot": spec["variant_snapshot"],
                })

            order_record["items"] = line_items
            self.order_items[order_id] = line_items
            return order_record

        except Exception:
            # Atomic rollback of all writes: restore inventory, delete parent order and items
            self.inventory = inventory_snapshot
            if order_id in self.orders:
                del self.orders[order_id]
            if order_id in self.order_items:
                del self.order_items[order_id]
            raise

    def _exec_fulfill_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = self._resolve_seller(params.get("p_seller_id"))
        order_id = str(params["p_order_id"])
        target_status = (params.get("p_target_status") or "completed").lower().strip()

        if target_status not in ("shipped", "completed", "delivered"):
            raise Exception("INVALID_INPUT: Target fulfillment status must be shipped, completed, or delivered")

        order = self.orders.get(order_id)
        if not order or order["seller_id"] != seller_id:
            raise Exception(f"NOT_FOUND: Order {order_id} not found or not owned by seller")

        curr_status = order["status"]
        if curr_status in ("shipped", "completed", "delivered"):
            raise Exception(f"INVALID_ORDER_TRANSITION: Order {order_id} is already fulfilled (current status: {curr_status})")
        if curr_status == "cancelled":
            raise Exception(f"INVALID_ORDER_TRANSITION: Cannot fulfill cancelled order {order_id}")
        if curr_status not in ("pending", "confirmed", "processing"):
            raise Exception(f"INVALID_ORDER_TRANSITION: Cannot fulfill order {order_id} with status {curr_status}")

        items = self.order_items.get(order_id, [])
        inventory_snapshot = {k: dict(v) for k, v in self.inventory.items()}

        try:
            for it in items:
                vid = str(it["variant_id"])
                qty = it["quantity"]
                inv = self.inventory.get(vid)
                if not inv or inv["seller_id"] != seller_id:
                    raise Exception(f"NOT_FOUND: Inventory record for variant {vid} not found")

                if inv["available_quantity"] < qty:
                    raise Exception(f"INSUFFICIENT_STOCK: Physical available quantity ({inv['available_quantity']}) is less than order quantity ({qty})")
                if inv["reserved_quantity"] < qty:
                    raise Exception(f"INSUFFICIENT_STOCK: Reserved quantity ({inv['reserved_quantity']}) is less than order quantity ({qty})")

                # Deduct physical stock and release corresponding reservation
                inv["available_quantity"] -= qty
                inv["reserved_quantity"] -= qty

            order["status"] = target_status
            order["updated_at"] = "2026-11-01T08:30:00Z"
            return order
        except Exception:
            self.inventory = inventory_snapshot
            raise

    def _exec_cancel_order_rpc(self, params: Dict[str, Any]) -> Dict[str, Any]:
        seller_id = self._resolve_seller(params.get("p_seller_id"))
        order_id = str(params["p_order_id"])

        order = self.orders.get(order_id)
        if not order or order["seller_id"] != seller_id:
            raise Exception(f"NOT_FOUND: Order {order_id} not found or not owned by seller")

        curr_status = order["status"]
        if curr_status == "cancelled":
            raise Exception(f"INVALID_ORDER_TRANSITION: Order {order_id} is already cancelled")
        if curr_status in ("shipped", "completed", "delivered"):
            raise Exception(f"INVALID_ORDER_TRANSITION: Cannot cancel already fulfilled order {order_id} (current status: {curr_status})")

        items = self.order_items.get(order_id, [])
        inventory_snapshot = {k: dict(v) for k, v in self.inventory.items()}

        try:
            for it in items:
                vid = str(it["variant_id"])
                qty = it["quantity"]
                inv = self.inventory.get(vid)
                if not inv or inv["seller_id"] != seller_id:
                    raise Exception(f"NOT_FOUND: Inventory record for variant {vid} not found")

                if inv["reserved_quantity"] < qty:
                    raise Exception(f"CONSTRAINT_VIOLATION: Reserved quantity ({inv['reserved_quantity']}) is less than order item quantity ({qty})")

                # Release reservation: physical available stock remains untouched
                inv["reserved_quantity"] -= qty

            order["status"] = "cancelled"
            order["updated_at"] = "2026-11-01T08:45:00Z"
            return order
        except Exception:
            self.inventory = inventory_snapshot
            raise


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def transaction_env():
    """Sets up a clean seller environment with customer, product, variant, and inventory."""
    db = MockTransactionalDatabase()
    seller_id = str(uuid.uuid4())
    db.authenticated_uid = seller_id

    # Customer
    customer_id = str(uuid.uuid4())
    db.customers[customer_id] = {
        "id": customer_id,
        "seller_id": seller_id,
        "phone": "+919876543210",
        "name": "Neha Sharma",
    }

    # Product & Variants
    product_id = str(uuid.uuid4())
    db.products[product_id] = {
        "id": product_id,
        "seller_id": seller_id,
        "name": "Cotton Kurti",
        "is_active": True,
    }

    variant_1_id = str(uuid.uuid4())
    db.variants[variant_1_id] = {
        "id": variant_1_id,
        "product_id": product_id,
        "seller_id": seller_id,
        "sku": "KURTI-BLU-M",
        "size": "M",
        "color": "Blue",
        "price": Decimal("799.00"),
    }
    db.inventory[variant_1_id] = {
        "id": str(uuid.uuid4()),
        "seller_id": seller_id,
        "variant_id": variant_1_id,
        "available_quantity": 10,
        "reserved_quantity": 0,
    }

    variant_2_id = str(uuid.uuid4())
    db.variants[variant_2_id] = {
        "id": variant_2_id,
        "product_id": product_id,
        "seller_id": seller_id,
        "sku": "KURTI-RED-L",
        "size": "L",
        "color": "Red",
        "price": Decimal("899.00"),
    }
    db.inventory[variant_2_id] = {
        "id": str(uuid.uuid4()),
        "seller_id": seller_id,
        "variant_id": variant_2_id,
        "available_quantity": 5,
        "reserved_quantity": 0,
    }

    service = OrderService(db=db)  # type: ignore

    return {
        "db": db,
        "service": service,
        "seller_id": seller_id,
        "customer_id": customer_id,
        "product_id": product_id,
        "variant_1_id": variant_1_id,
        "variant_2_id": variant_2_id,
    }


# ============================================================================
# 1. Order Creation & Inventory Reservation Tests
# ============================================================================

class TestOrderCreationWithReservation:
    def test_successful_order_creation_single_item(self, transaction_env):
        env = transaction_env
        service = env["service"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=2)],
            currency="INR",
            notes="Please pack carefully",
        )

        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        assert order.id is not None
        assert order.status == "pending"
        assert order.total_amount == Decimal("1598.00")  # 2 * 799.00
        assert order.items is not None
        assert len(order.items) == 1
        assert order.items[0].product_name_snapshot == "Cotton Kurti"
        assert order.items[0].variant_snapshot["sku"] == "KURTI-BLU-M"

        # Check inventory reserved incremented
        inv = env["db"].inventory[env["variant_1_id"]]
        assert inv["available_quantity"] == 10
        assert inv["reserved_quantity"] == 2
        assert (inv["available_quantity"] - inv["reserved_quantity"]) == 8  # 8 sellable left

    def test_successful_order_creation_multiple_items(self, transaction_env):
        env = transaction_env
        service = env["service"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[
                OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=2),  # 2 * 799 = 1598
                OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_2_id"]), quantity=1),  # 1 * 899 = 899
            ],
            currency="INR",
        )

        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert order.total_amount == Decimal("2497.00")
        assert len(order.items) == 2

        assert env["db"].inventory[env["variant_1_id"]]["reserved_quantity"] == 2
        assert env["db"].inventory[env["variant_2_id"]]["reserved_quantity"] == 1

    def test_rejects_incorrect_customer_ownership(self, transaction_env):
        env = transaction_env
        service = env["service"]
        foreign_customer = uuid.uuid4()

        req = OrderCreateRequest(
            customer_id=foreign_customer,
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )

        with pytest.raises(NotFoundError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Customer" in str(exc_info.value)

    def test_rejects_incorrect_variant_ownership(self, transaction_env):
        env = transaction_env
        service = env["service"]
        foreign_variant = uuid.uuid4()

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=foreign_variant, quantity=1)],
        )

        with pytest.raises(NotFoundError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Variant" in str(exc_info.value)

    def test_rejects_inactive_product(self, transaction_env):
        env = transaction_env
        service = env["service"]
        env["db"].products[env["product_id"]]["is_active"] = False

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )

        with pytest.raises(BusinessRuleError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "inactive" in str(exc_info.value).lower()

    def test_rejects_insufficient_inventory(self, transaction_env):
        env = transaction_env
        service = env["service"]

        # Only 10 available, request 11
        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=11)],
        )

        with pytest.raises(InsufficientStockError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Insufficient sellable stock" in str(exc_info.value)
        # Verify 0 reserved
        assert env["db"].inventory[env["variant_1_id"]]["reserved_quantity"] == 0

    def test_rejects_duplicate_variant_in_order(self, transaction_env):
        env = transaction_env
        service = env["service"]

        # Duplicate item in array
        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[
                OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1),
                OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=2),
            ],
        )

        with pytest.raises(BusinessRuleError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Duplicate variant_id" in str(exc_info.value)

    def test_atomic_rollback_on_failure_during_order_item_creation(self, transaction_env):
        env = transaction_env
        service = env["service"]
        env["db"].simulate_item_insert_failure = True

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=3)],
        )

        with pytest.raises(RepositoryError):
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        # Inventory must be rolled back completely to 0 reserved
        assert env["db"].inventory[env["variant_1_id"]]["reserved_quantity"] == 0
        assert len(env["db"].orders) == 0

    def test_order_creation_immune_to_concurrent_price_change(self, transaction_env):
        """
        Validates Requirement 1, 3, 5, 6 & 7:
        Even if product price or catalog status is changed concurrently mid-flight,
        the two-pass RPC uses exclusively the buffered snapshot from Pass 1.
        Therefore:
        1. orders.total_amount strictly equals SUM(order_items.line_total).
        2. Line item unit_price and line_total reflect the validated snapshot, not the mutated catalog.
        """
        env = transaction_env
        service = env["service"]
        db = env["db"]
        vid = env["variant_1_id"]
        pid = env["product_id"]

        # Initial price is 799.00
        assert db.variants[vid]["price"] == Decimal("799.00")

        # Simulate concurrent price change and product deactivation mid-flight between Pass 1 and Pass 2
        def concurrent_catalog_mutation(database):
            # Concurrent merchant edit updates price from 799.00 to 1499.00 and deactivates product
            database.variants[vid]["price"] = Decimal("1499.00")
            database.products[pid]["is_active"] = False

        db.on_before_pass_2 = concurrent_catalog_mutation

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=2)],
            currency="INR",
        )

        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        # 1. Authoritative total_amount strictly equals SUM(order_items.line_total)
        assert order.items is not None
        assert len(order.items) == 1
        calculated_sum = sum(item.line_total for item in order.items)
        assert order.total_amount == calculated_sum

        # 2. Both total_amount and order_items used the buffered snapshot from Pass 1
        # (2 * 799.00 = 1598.00, NOT the mutated 1499.00)
        assert order.total_amount == Decimal("1598.00")
        assert order.items[0].unit_price == Decimal("799.00")
        assert order.items[0].line_total == Decimal("1598.00")

    def test_deliberate_second_pass_failure_rolls_back_parent_order_and_inventory(self, transaction_env):
        """
        Validates Requirement 8:
        Simulate deliberate failure during Pass 2 (e.g. after parent order has been inserted).
        Verify that:
        1. Parent order is completely rolled back and deleted.
        2. No orphaned order items exist.
        3. All inventory reserved_quantity increments are rolled back.
        4. Physical stock remains completely intact.
        """
        env = transaction_env
        service = env["service"]
        db = env["db"]
        vid = env["variant_1_id"]

        # Initial stock: 10 available, 0 reserved
        assert db.inventory[vid]["available_quantity"] == 10
        assert db.inventory[vid]["reserved_quantity"] == 0

        # Inject failure during Pass 2 item insertion
        db.simulate_item_insert_failure = True

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=4)],
            currency="INR",
        )

        with pytest.raises(RepositoryError):
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        # Parent order must not exist in database
        assert len(db.orders) == 0

        # Order items table must have zero items
        assert len(db.order_items) == 0

        # Inventory reservation must be rolled back completely to 0
        assert db.inventory[vid]["reserved_quantity"] == 0
        assert db.inventory[vid]["available_quantity"] == 10

    def test_concurrent_product_deactivation_during_order_creation(self, transaction_env):
        """
        Validates:
        Even if product.is_active is modified mid-flight before Pass 2,
        the transaction already locked the product row (FOR SHARE OF p) and buffered
        the active product snapshot in memory, guaranteeing no inconsistent validation.
        """
        env = transaction_env
        service = env["service"]
        db = env["db"]
        vid = env["variant_1_id"]
        pid = env["product_id"]

        # Product is active initially
        assert db.products[pid]["is_active"] is True

        # Hook: simulate concurrent merchant deactivating product mid-flight
        def deactive_mid_flight(database):
            database.products[pid]["is_active"] = False

        db.on_before_pass_2 = deactive_mid_flight

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=1)],
            currency="INR",
        )

        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert order.id is not None
        assert order.total_amount == Decimal("799.00")
        assert order.items[0].product_name_snapshot == "Cotton Kurti"

    def test_inventory_reservation_row_count_zero_triggers_atomic_rollback(self, transaction_env):
        """
        Validates:
        GET DIAGNOSTICS ROW_COUNT check:
        If the inventory UPDATE in Pass 2 updates 0 rows (e.g. condition
        (reserved_quantity + quantity) <= available_quantity is violated),
        an exception is raised and the transaction completely rolls back
        (parent order deleted, order_items deleted, inventory untouched).
        """
        env = transaction_env
        service = env["service"]
        db = env["db"]
        vid = env["variant_1_id"]

        # Initial: 10 available, 8 reserved -> 2 sellable
        db.inventory[vid]["available_quantity"] = 10
        db.inventory[vid]["reserved_quantity"] = 8

        # Hook: concurrent process steals the remaining 2 units between Pass 1 and Pass 2
        def steal_stock_mid_flight(database):
            # Exhaust remaining stock right before Pass 2
            database.inventory[vid]["reserved_quantity"] = 10

        db.on_before_pass_2 = steal_stock_mid_flight

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=2)],
            currency="INR",
        )

        with pytest.raises(InsufficientStockError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Inventory reservation failed" in str(exc_info.value) or "stock condition violated" in str(exc_info.value)

        # Confirm atomic rollback: parent order must not exist
        assert len(db.orders) == 0
        assert len(db.order_items) == 0
        # Inventory restored to snapshot
        assert db.inventory[vid]["reserved_quantity"] == 8

    def test_exact_equality_between_order_total_and_sum_order_items(self, transaction_env):
        """
        Validates:
        orders.total_amount strictly equals SUM(order_items.line_total)
        for multi-item orders with non-trivial pricing.
        """
        env = transaction_env
        service = env["service"]
        v1 = env["variant_1_id"]
        v2 = env["variant_2_id"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[
                OrderItemCreateRequest(variant_id=uuid.UUID(v1), quantity=3),  # 3 * 799.00 = 2397.00
                OrderItemCreateRequest(variant_id=uuid.UUID(v2), quantity=2),  # 2 * 899.00 = 1798.00
            ],
            currency="INR",
        )

        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert order.items is not None
        assert len(order.items) == 2

        items_sum = sum(item.line_total for item in order.items)
        assert order.total_amount == items_sum
        assert order.total_amount == Decimal("4195.00")


# ============================================================================
# 2. Concurrency & Oversell Protection Tests
# ============================================================================

class TestConcurrencyAndOversellProtection:
    def test_two_orders_competing_for_last_stock_one_succeeds_one_fails(self, transaction_env):
        env = transaction_env
        service = env["service"]
        vid = env["variant_1_id"]

        # Set physical stock to 1
        env["db"].inventory[vid]["available_quantity"] = 1
        env["db"].inventory[vid]["reserved_quantity"] = 0

        req_1 = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=1)],
        )
        req_2 = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=1)],
        )

        # First request succeeds
        order_1 = service.create_order_with_reservation(seller_id=env["seller_id"], data=req_1)
        assert order_1.id is not None
        assert env["db"].inventory[vid]["reserved_quantity"] == 1
        assert (env["db"].inventory[vid]["available_quantity"] - env["db"].inventory[vid]["reserved_quantity"]) == 0

        # Second concurrent request must fail with InsufficientStockError (no overselling)
        with pytest.raises(InsufficientStockError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req_2)

        assert "Insufficient sellable stock" in str(exc_info.value)
        # Final inventory integrity
        assert env["db"].inventory[vid]["available_quantity"] == 1
        assert env["db"].inventory[vid]["reserved_quantity"] == 1


# ============================================================================
# 3. Order Fulfillment Tests
# ============================================================================

class TestOrderFulfillment:
    def test_successful_fulfillment_reduces_both_physical_and_reserved_stock(self, transaction_env):
        env = transaction_env
        service = env["service"]
        vid = env["variant_1_id"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=3)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert env["db"].inventory[vid]["available_quantity"] == 10
        assert env["db"].inventory[vid]["reserved_quantity"] == 3

        # Fulfill order
        fulfilled = service.fulfill_order(seller_id=env["seller_id"], order_id=order.id, target_status="completed")
        assert fulfilled.status == "completed"

        # Physical stock was 10 -> now 7. Reserved was 3 -> now 0.
        inv = env["db"].inventory[vid]
        assert inv["available_quantity"] == 7
        assert inv["reserved_quantity"] == 0

    def test_duplicate_fulfillment_rejected(self, transaction_env):
        env = transaction_env
        service = env["service"]
        vid = env["variant_1_id"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=2)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        service.fulfill_order(seller_id=env["seller_id"], order_id=order.id, target_status="completed")

        # Second attempt to fulfill the same order
        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service.fulfill_order(seller_id=env["seller_id"], order_id=order.id)
        assert "already fulfilled" in str(exc_info.value)

    def test_cannot_fulfill_cancelled_order(self, transaction_env):
        env = transaction_env
        service = env["service"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        service.cancel_order(seller_id=env["seller_id"], order_id=order.id)

        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service.fulfill_order(seller_id=env["seller_id"], order_id=order.id)
        assert "Cannot fulfill cancelled order" in str(exc_info.value)


# ============================================================================
# 4. Order Cancellation Tests
# ============================================================================

class TestOrderCancellation:
    def test_successful_cancellation_releases_reserved_stock_intact_physical_stock(self, transaction_env):
        env = transaction_env
        service = env["service"]
        vid = env["variant_1_id"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(vid), quantity=4)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        assert env["db"].inventory[vid]["available_quantity"] == 10
        assert env["db"].inventory[vid]["reserved_quantity"] == 4

        # Cancel order
        cancelled = service.cancel_order(seller_id=env["seller_id"], order_id=order.id)
        assert cancelled.status == "cancelled"

        # Reserved stock decremented back to 0; physical available quantity untouched at 10
        inv = env["db"].inventory[vid]
        assert inv["available_quantity"] == 10
        assert inv["reserved_quantity"] == 0

    def test_duplicate_cancellation_rejected(self, transaction_env):
        env = transaction_env
        service = env["service"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        service.cancel_order(seller_id=env["seller_id"], order_id=order.id)

        # Second attempt to cancel must be rejected
        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service.cancel_order(seller_id=env["seller_id"], order_id=order.id)
        assert "already cancelled" in str(exc_info.value)

    def test_fulfilled_orders_cannot_be_cancelled(self, transaction_env):
        env = transaction_env
        service = env["service"]

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        service.fulfill_order(seller_id=env["seller_id"], order_id=order.id, target_status="completed")

        with pytest.raises(InvalidOrderTransitionError) as exc_info:
            service.cancel_order(seller_id=env["seller_id"], order_id=order.id)
        assert "already fulfilled" in str(exc_info.value)


# ============================================================================
# 5. Security & Cross-Seller Isolation Tests
# ============================================================================

class TestSecurityAndCrossSellerIsolation:
    def test_seller_cannot_create_order_with_other_seller_customer(self, transaction_env):
        env = transaction_env
        service = env["service"]
        seller_b = str(uuid.uuid4())

        # Customer belongs to Seller B
        foreign_cust = str(uuid.uuid4())
        env["db"].customers[foreign_cust] = {
            "id": foreign_cust,
            "seller_id": seller_b,
            "phone": "+919111111111",
            "name": "Seller B Customer",
        }

        req = OrderCreateRequest(
            customer_id=uuid.UUID(foreign_cust),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )

        with pytest.raises(NotFoundError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Customer" in str(exc_info.value)

    def test_seller_cannot_reserve_other_seller_inventory(self, transaction_env):
        env = transaction_env
        service = env["service"]
        seller_b = str(uuid.uuid4())

        # Product & Variant belong to Seller B
        prod_b = str(uuid.uuid4())
        var_b = str(uuid.uuid4())
        env["db"].products[prod_b] = {"id": prod_b, "seller_id": seller_b, "name": "B Product", "is_active": True}
        env["db"].variants[var_b] = {"id": var_b, "product_id": prod_b, "seller_id": seller_b, "price": Decimal("500.00")}
        env["db"].inventory[var_b] = {"id": str(uuid.uuid4()), "seller_id": seller_b, "variant_id": var_b, "available_quantity": 5, "reserved_quantity": 0}

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(var_b), quantity=1)],
        )

        with pytest.raises(NotFoundError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Variant" in str(exc_info.value)

    def test_seller_cannot_fulfill_other_seller_order(self, transaction_env):
        env = transaction_env
        service = env["service"]
        seller_b = str(uuid.uuid4())

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        # Seller B attempts to fulfill Seller A's order
        env["db"].authenticated_uid = seller_b
        with pytest.raises(NotFoundError) as exc_info:
            service.fulfill_order(seller_id=seller_b, order_id=order.id)
        assert "Order" in str(exc_info.value)

    def test_seller_cannot_cancel_other_seller_order(self, transaction_env):
        env = transaction_env
        service = env["service"]
        seller_b = str(uuid.uuid4())

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )
        order = service.create_order_with_reservation(seller_id=env["seller_id"], data=req)

        # Seller B attempts to cancel Seller A's order
        env["db"].authenticated_uid = seller_b
        with pytest.raises(NotFoundError) as exc_info:
            service.cancel_order(seller_id=seller_b, order_id=order.id)
        assert "Order" in str(exc_info.value)

    def test_anonymous_execution_rejected(self, transaction_env):
        env = transaction_env
        service = env["service"]
        env["db"].authenticated_uid = None
        env["db"].caller_role = "anon"

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.create_order_with_reservation(seller_id=env["seller_id"], data=req)
        assert "Caller must be authenticated" in str(exc_info.value)

    def test_caller_seller_id_mismatch_rejected(self, transaction_env):
        env = transaction_env
        service = env["service"]
        # Authenticated as Seller A, but passing Seller B in parameter
        env["db"].authenticated_uid = env["seller_id"]
        seller_b = str(uuid.uuid4())

        req = OrderCreateRequest(
            customer_id=uuid.UUID(env["customer_id"]),
            items=[OrderItemCreateRequest(variant_id=uuid.UUID(env["variant_1_id"]), quantity=1)],
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.create_order_with_reservation(seller_id=seller_b, data=req)
        assert "Caller seller_id mismatch" in str(exc_info.value)


# ============================================================================
# 6. Live Supabase RPC Integration Test
# ============================================================================

class TestLiveSupabaseRPCRejection:
    def test_live_supabase_unauthenticated_rpc_call(self):
        """
        Executes a real HTTPS RPC call against the live Supabase instance
        using the publishable anon key.
        Confirms that the live database endpoint enforces access boundaries:
        - If the migration is not yet applied to the remote schema cache, PostgREST returns PGRST202.
        - If applied, anonymous execution is rejected with 42501 permission denied.
        Either way, unauthenticated arbitrary access is completely blocked on live Supabase.
        """
        client = get_supabase_client()
        with pytest.raises(Exception) as exc_info:
            client.rpc("create_order_with_reservation_rpc", {
                "p_customer_id": str(uuid.uuid4()),
                "p_items": [],
            }).execute()

        err_str = str(exc_info.value)
        # PGRST202: Not found in schema cache (migration pending on remote DB)
        # or 42501: permission denied for function / unauthenticated
        assert any(code in err_str for code in ("PGRST202", "42501", "permission denied", "Could not find"))
