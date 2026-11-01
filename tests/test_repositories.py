import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from backend.app.schemas.customer import CustomerCreateRequest, CustomerUpdateRequest
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
)
from backend.app.schemas.inventory import InventoryUpdateRequest
from backend.app.schemas.payment import PaymentCreateRequest, PaymentMethod, PaymentStatus

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.order_repository import OrderRepository
from backend.app.repositories.payment_repository import PaymentRepository

from backend.app.repositories.exceptions import (
    NotFoundError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    PermissionDeniedError,
    ConstraintViolationError,
    DatabaseConnectionError,
    map_supabase_error,
)


# ============================================================================
# In-Memory Mock PostgREST Client for Unit Testing
# ============================================================================

class InMemoryQuery:
    def __init__(self, table_name: str, in_memory_store: dict):
        self.table_name = table_name
        self.store = in_memory_store
        self.rows = list(self.store.get(table_name, []))
        self._action = "select"
        self._payload = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, column: str, value: str):
        self.rows = [r for r in self.rows if str(r.get(column)) == str(value)]
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


class InMemoryMockClient:
    def __init__(self, initial_data: dict = None):
        self.store = initial_data or {
            "customers": [],
            "products": [],
            "product_variants": [],
            "inventory": [],
            "orders": [],
            "order_items": [],
            "payments": [],
        }

    def table(self, name: str):
        if name not in self.store:
            self.store[name] = []
        return InMemoryQuery(name, self.store)


# ============================================================================
# CustomerRepository Tests (Mocked)
# ============================================================================

class TestCustomerRepository:
    def test_create_and_get_customer_success(self):
        client = InMemoryMockClient()
        repo = CustomerRepository(client)
        seller_id = uuid.uuid4()

        req = CustomerCreateRequest(phone="+919876543210", name="Neha Sharma", notes="VIP Customer")
        cust = repo.create_customer(seller_id=seller_id, data=req)

        assert cust.phone == "+919876543210"
        assert cust.name == "Neha Sharma"
        assert str(cust.seller_id) == str(seller_id)

        # Fetch by ID
        fetched = repo.get_customer_by_id(seller_id=seller_id, customer_id=cust.id)
        assert fetched is not None
        assert fetched.id == cust.id

        # Fetch by phone
        fetched_phone = repo.get_customer_by_phone(seller_id=seller_id, phone="9876543210")
        assert fetched_phone is not None
        assert fetched_phone.id == cust.id

    def test_create_customer_rejects_duplicate_phone(self):
        client = InMemoryMockClient()
        repo = CustomerRepository(client)
        seller_id = uuid.uuid4()

        req1 = CustomerCreateRequest(phone="+919876543210", name="First")
        repo.create_customer(seller_id=seller_id, data=req1)

        req2 = CustomerCreateRequest(phone="+919876543210", name="Second")
        with pytest.raises(DuplicateRecordError) as exc_info:
            repo.create_customer(seller_id=seller_id, data=req2)
        assert "already exists for this seller" in str(exc_info.value)

    def test_customer_cross_seller_isolation(self):
        client = InMemoryMockClient()
        repo = CustomerRepository(client)
        seller_a = uuid.uuid4()
        seller_b = uuid.uuid4()

        cust = repo.create_customer(seller_id=seller_a, data=CustomerCreateRequest(phone="+919876543210", name="A"))

        # Seller B cannot see Seller A's customer
        assert repo.get_customer_by_id(seller_id=seller_b, customer_id=cust.id) is None
        assert repo.get_customer_by_phone(seller_id=seller_b, phone="+919876543210") is None

        # Seller B CAN create a customer with the same phone number (independent tenant namespace)
        cust_b = repo.create_customer(seller_id=seller_b, data=CustomerCreateRequest(phone="+919876543210", name="B"))
        assert cust_b.id != cust.id
        assert str(cust_b.seller_id) == str(seller_b)

    def test_list_customers_pagination(self):
        client = InMemoryMockClient()
        repo = CustomerRepository(client)
        seller_id = uuid.uuid4()

        for i in range(5):
            repo.create_customer(seller_id=seller_id, data=CustomerCreateRequest(phone=f"+91987654321{i}", name=f"User {i}"))

        page1 = repo.list_customers(seller_id=seller_id, limit=3, offset=0)
        assert len(page1) == 3

        page2 = repo.list_customers(seller_id=seller_id, limit=3, offset=3)
        assert len(page2) == 2

    def test_update_customer_and_delete(self):
        client = InMemoryMockClient()
        repo = CustomerRepository(client)
        seller_id = uuid.uuid4()

        cust = repo.create_customer(seller_id=seller_id, data=CustomerCreateRequest(phone="+919876543210", name="Old Name"))
        updated = repo.update_customer(seller_id=seller_id, customer_id=cust.id, data=CustomerUpdateRequest(name="New Name"))
        assert updated is not None
        assert updated.name == "New Name"

        deleted = repo.delete_customer(seller_id=seller_id, customer_id=cust.id)
        assert deleted is True
        assert repo.get_customer_by_id(seller_id=seller_id, customer_id=cust.id) is None


# ============================================================================
# ProductRepository Tests (Mocked)
# ============================================================================

class TestProductRepository:
    def test_create_product_and_variant_success(self):
        client = InMemoryMockClient()
        repo = ProductRepository(client)
        seller_id = uuid.uuid4()

        prod = repo.create_product(
            seller_id=seller_id,
            data=ProductCreateRequest(name="Anarkali Suit", category="Ethnic", is_active=True)
        )
        assert prod.name == "Anarkali Suit"
        assert str(prod.seller_id) == str(seller_id)

        # Create variant
        var = repo.create_variant(
            seller_id=seller_id,
            data=ProductVariantCreateRequest(
                product_id=prod.id,
                sku="AS-XL-RED",
                size="XL",
                color="Red",
                price=Decimal("1299.00")
            )
        )
        assert var.sku == "AS-XL-RED"
        assert var.price == Decimal("1299.00")
        assert var.product_id == prod.id

        # List variants
        vars_list = repo.list_variants_by_product(seller_id=seller_id, product_id=prod.id)
        assert len(vars_list) == 1
        assert vars_list[0].id == var.id

    def test_variant_creation_rejects_cross_seller_product(self):
        client = InMemoryMockClient()
        repo = ProductRepository(client)
        seller_a = uuid.uuid4()
        seller_b = uuid.uuid4()

        prod_a = repo.create_product(seller_id=seller_a, data=ProductCreateRequest(name="Seller A Dress"))

        # Seller B attempts to create variant under Seller A's product
        with pytest.raises(ForeignKeyViolationError):
            repo.create_variant(
                seller_id=seller_b,
                data=ProductVariantCreateRequest(
                    product_id=prod_a.id,
                    price=Decimal("500.00")
                )
            )

    def test_archive_product_soft_delete(self):
        client = InMemoryMockClient()
        repo = ProductRepository(client)
        seller_id = uuid.uuid4()

        prod = repo.create_product(seller_id=seller_id, data=ProductCreateRequest(name="Seasonal Item", is_active=True))
        assert prod.is_active is True

        archived = repo.archive_product(seller_id=seller_id, product_id=prod.id)
        assert archived is True

        fetched = repo.get_product_by_id(seller_id=seller_id, product_id=prod.id)
        assert fetched.is_active is False


# ============================================================================
# InventoryRepository Tests (Mocked)
# ============================================================================

class TestInventoryRepository:
    def test_inventory_read_and_update(self):
        seller_id = uuid.uuid4()
        var_id = uuid.uuid4()
        inv_id = uuid.uuid4()
        initial_data = {
            "inventory": [{
                "id": str(inv_id),
                "seller_id": str(seller_id),
                "variant_id": str(var_id),
                "available_quantity": 20,
                "reserved_quantity": 2,
                "low_stock_threshold": 5,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }]
        }
        client = InMemoryMockClient(initial_data)
        repo = InventoryRepository(client)

        inv = repo.get_inventory_by_variant(seller_id=seller_id, variant_id=var_id)
        assert inv is not None
        assert inv.available_quantity == 20

        # Update available quantity
        updated = repo.update_inventory(
            seller_id=seller_id,
            variant_id=var_id,
            data=InventoryUpdateRequest(available_quantity=15)
        )
        assert updated is not None
        assert updated.available_quantity == 15
        assert updated.reserved_quantity == 2

    def test_inventory_rejects_negative_bounds(self):
        client = InMemoryMockClient()
        repo = InventoryRepository(client)
        seller_id = uuid.uuid4()
        var_id = uuid.uuid4()

        with pytest.raises(ConstraintViolationError):
            repo.update_inventory(
                seller_id=seller_id,
                variant_id=var_id,
                data=InventoryUpdateRequest.model_construct(available_quantity=-5)
            )


# ============================================================================
# OrderRepository Tests (Mocked)
# ============================================================================

class TestOrderRepository:
    def test_get_orders_and_order_items(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        ord_id = uuid.uuid4()
        var_id = uuid.uuid4()

        initial_data = {
            "orders": [{
                "id": str(ord_id),
                "seller_id": str(seller_id),
                "customer_id": str(cust_id),
                "status": "pending",
                "total_amount": 998.00,
                "currency": "INR",
                "notes": "Fragile shipment",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }],
            "order_items": [{
                "id": str(uuid.uuid4()),
                "order_id": str(ord_id),
                "seller_id": str(seller_id),
                "variant_id": str(var_id),
                "quantity": 2,
                "unit_price": 499.00,
                "line_total": 998.00,
                "product_name_snapshot": "Blue Kurti",
                "variant_snapshot": {"size": "M"}
            }]
        }
        client = InMemoryMockClient(initial_data)
        repo = OrderRepository(client)

        order = repo.get_order_by_id(seller_id=seller_id, order_id=ord_id)
        assert order is not None
        assert order.status == "pending"
        assert order.total_amount == Decimal("998.00")

        # Get line items
        items = repo.get_order_items(seller_id=seller_id, order_id=ord_id)
        assert len(items) == 1
        assert items[0].product_name_snapshot == "Blue Kurti"
        assert items[0].quantity == 2

        # Customer orders list
        cust_orders = repo.get_orders_by_customer(seller_id=seller_id, customer_id=cust_id)
        assert len(cust_orders) == 1


# ============================================================================
# PaymentRepository Tests (Mocked)
# ============================================================================

class TestPaymentRepository:
    def test_payment_creation_rejects_unlinked_payments(self):
        client = InMemoryMockClient()
        repo = PaymentRepository(client)
        seller_id = uuid.uuid4()

        req = PaymentCreateRequest(
            order_id=None,
            amount=Decimal("500.00"),
            method=PaymentMethod.UPI
        )
        with pytest.raises(ConstraintViolationError) as exc_info:
            repo.create_payment(seller_id=seller_id, data=req)
        assert "live database schema requires 'order_id'" in str(exc_info.value)

    def test_payment_creation_rejects_cross_seller_order(self):
        seller_a = uuid.uuid4()
        seller_b = uuid.uuid4()
        ord_a = uuid.uuid4()

        initial_data = {
            "orders": [{
                "id": str(ord_a),
                "seller_id": str(seller_a),
                "customer_id": str(uuid.uuid4()),
                "status": "pending",
                "total_amount": 500.00,
                "currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }]
        }
        client = InMemoryMockClient(initial_data)
        repo = PaymentRepository(client)

        req = PaymentCreateRequest(
            order_id=ord_a,
            amount=Decimal("500.00"),
            method=PaymentMethod.UPI
        )
        with pytest.raises(ForeignKeyViolationError):
            repo.create_payment(seller_id=seller_b, data=req)

    def test_create_and_find_payment_success(self):
        seller_id = uuid.uuid4()
        ord_id = uuid.uuid4()
        initial_data = {
            "orders": [{
                "id": str(ord_id),
                "seller_id": str(seller_id),
                "customer_id": str(uuid.uuid4()),
                "status": "pending",
                "total_amount": 1000.00,
                "currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }],
            "payments": []
        }
        client = InMemoryMockClient(initial_data)
        repo = PaymentRepository(client)

        req = PaymentCreateRequest(
            order_id=ord_id,
            amount=Decimal("1000.00"),
            method=PaymentMethod.UPI,
            status=PaymentStatus.PENDING,
            transaction_reference="UPI/2026/TXN987654"
        )
        pay = repo.create_payment(seller_id=seller_id, data=req)
        assert pay.amount == Decimal("1000.00")
        assert pay.status == PaymentStatus.PENDING

        # Find by transaction reference
        found = repo.find_payment_by_transaction_reference(seller_id=seller_id, reference="UPI/2026/TXN987654")
        assert found is not None
        assert found.id == pay.id

        # List payments by order
        order_pays = repo.get_payments_by_order(seller_id=seller_id, order_id=ord_id)
        assert len(order_pays) == 1


# ============================================================================
# Error Mapping & Security Exception Tests
# ============================================================================

class TestErrorMapping:
    def test_map_supabase_error_rls_permission_denied(self):
        err = Exception("new row violates row-level security policy for table 'customers' (code: 42501)")
        repo_err = map_supabase_error(err, entity="Customer")
        assert isinstance(repo_err, PermissionDeniedError)
        assert "RLS policy violation" in str(repo_err)

    def test_map_supabase_error_duplicate_key(self):
        err = Exception("duplicate key value violates unique constraint 'customers_phone_key' (code: 23505)")
        repo_err = map_supabase_error(err, entity="Customer")
        assert isinstance(repo_err, DuplicateRecordError)
        assert "already exists" in str(repo_err)

    def test_map_supabase_error_foreign_key_violation(self):
        err = Exception("insert or update on table 'product_variants' violates foreign key constraint 'product_variants_product_id_fkey' (code: 23503)")
        repo_err = map_supabase_error(err, entity="ProductVariant")
        assert isinstance(repo_err, ForeignKeyViolationError)
        assert "Referenced foreign key" in str(repo_err)

    def test_map_supabase_error_connection_timeout(self):
        err = Exception("HTTPSConnectionPool(host='yomqkdgofwsmzrpbxxag.supabase.co', port=443): Read timed out.")
        repo_err = map_supabase_error(err, entity="Database")
        assert isinstance(repo_err, DatabaseConnectionError)
        assert "connection failure" in str(repo_err)
