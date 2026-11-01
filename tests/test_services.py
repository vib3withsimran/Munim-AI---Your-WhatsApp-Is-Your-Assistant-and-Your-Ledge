import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest

from backend.app.schemas.customer import CustomerCreateRequest, CustomerUpdateRequest
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductVariantCreateRequest,
)
from backend.app.schemas.inventory import InventoryUpdateRequest
from backend.app.schemas.order import OrderCreateRequest, OrderItemCreateRequest, OrderStatus
from backend.app.schemas.payment import PaymentCreateRequest, PaymentMethod, PaymentStatus

from backend.app.services.customer_service import CustomerService
from backend.app.services.product_service import ProductService
from backend.app.services.inventory_service import InventoryService
from backend.app.services.order_service import OrderService
from backend.app.services.payment_service import PaymentService

from backend.app.repositories.exceptions import (
    NotFoundError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    ConstraintViolationError,
)
from backend.app.services.exceptions import (
    InsufficientStockError,
    InvalidOrderTransitionError,
    InvalidPaymentTransitionError,
    AmbiguousPaymentMatchError,
)
from tests.test_repositories import InMemoryMockClient


# ============================================================================
# Customer Service Tests (Mocked)
# ============================================================================

class TestCustomerService:
    def test_create_customer_normalizes_phone_and_detects_duplicate(self):
        client = InMemoryMockClient()
        service = CustomerService(client)
        seller_id = uuid.uuid4()

        cust = service.create_customer(
            seller_id=seller_id,
            data=CustomerCreateRequest(phone="+91 (987) 654-3210", name="Aarti")
        )
        assert cust.phone == "+919876543210"

        # Duplicate detection with 10-digit format
        with pytest.raises(DuplicateRecordError):
            service.create_customer(
                seller_id=seller_id,
                data=CustomerCreateRequest(phone="9876543210", name="Aarti Duplicate")
            )

    def test_archive_customer_preserves_orders_and_updates_notes(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        initial_data = {
            "customers": [{
                "id": str(cust_id),
                "seller_id": str(seller_id),
                "phone": "+919876543210",
                "name": "Cust With Order",
                "notes": "Prefers evening deliveries",
                "created_at": datetime.now(timezone.utc).isoformat()
            }],
            "orders": [{
                "id": str(uuid.uuid4()),
                "seller_id": str(seller_id),
                "customer_id": str(cust_id),
                "status": "pending",
                "total_amount": 500.0,
                "currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }],
            "privacy_settings": []
        }
        client = InMemoryMockClient(initial_data)
        service = CustomerService(client)

        archived = service.archive_customer(seller_id=seller_id, customer_id=cust_id)
        assert archived is True

        # Check customer record is preserved and notes updated
        cust = service.get_customer(seller_id=seller_id, customer_id=cust_id)
        assert cust is not None
        assert "[ARCHIVED]" in cust.notes

    def test_archive_customer_deletes_when_no_orders(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        initial_data = {
            "customers": [{
                "id": str(cust_id),
                "seller_id": str(seller_id),
                "phone": "+919876543210",
                "name": "Cust No Order",
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }],
            "orders": [],
            "privacy_settings": []
        }
        client = InMemoryMockClient(initial_data)
        service = CustomerService(client)

        archived = service.archive_customer(seller_id=seller_id, customer_id=cust_id)
        assert archived is True
        assert service.get_customer(seller_id=seller_id, customer_id=cust_id) is None

    def test_customer_privacy_setting_and_retrieval(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        initial_data = {
            "customers": [{
                "id": str(cust_id),
                "seller_id": str(seller_id),
                "phone": "+919876543210",
                "name": "Private Customer",
                "notes": None,
                "created_at": datetime.now(timezone.utc).isoformat()
            }],
            "privacy_settings": []
        }
        client = InMemoryMockClient(initial_data)
        service = CustomerService(client)

        assert service.is_customer_private(seller_id=seller_id, customer_id=cust_id) is False
        service.set_customer_privacy(seller_id=seller_id, customer_id=cust_id, is_private=True)
        assert service.is_customer_private(seller_id=seller_id, customer_id=cust_id) is True


# ============================================================================
# Product Service Tests (Mocked)
# ============================================================================

class TestProductService:
    def test_product_and_variant_creation_ownership(self):
        client = InMemoryMockClient()
        service = ProductService(client)
        seller_id = uuid.uuid4()

        prod = service.create_product(seller_id=seller_id, data=ProductCreateRequest(name="Cotton Saree"))
        var = service.create_variant(
            seller_id=seller_id,
            data=ProductVariantCreateRequest(
                product_id=prod.id,
                sku="CS-RED",
                color="Red",
                price=Decimal("1500.00")
            )
        )
        assert var.price == Decimal("1500.00")
        assert var.product_id == prod.id

    def test_variant_creation_blocked_on_archived_product(self):
        client = InMemoryMockClient()
        service = ProductService(client)
        seller_id = uuid.uuid4()

        prod = service.create_product(seller_id=seller_id, data=ProductCreateRequest(name="Discontinued Item"))
        service.archive_product(seller_id=seller_id, product_id=prod.id)

        with pytest.raises(ForeignKeyViolationError) as exc_info:
            service.create_variant(
                seller_id=seller_id,
                data=ProductVariantCreateRequest(
                    product_id=prod.id,
                    price=Decimal("200.00")
                )
            )
        assert "Cannot add variant to archived product" in str(exc_info.value)

    def test_product_catalog_excludes_archived_products(self):
        client = InMemoryMockClient()
        service = ProductService(client)
        seller_id = uuid.uuid4()

        p1 = service.create_product(seller_id=seller_id, data=ProductCreateRequest(name="Active Kurti"))
        service.create_variant(seller_id=seller_id, data=ProductVariantCreateRequest(product_id=p1.id, price=Decimal("699.00")))

        p2 = service.create_product(seller_id=seller_id, data=ProductCreateRequest(name="Archived Kurti"))
        service.archive_product(seller_id=seller_id, product_id=p2.id)

        catalog = service.get_product_catalog(seller_id=seller_id)
        assert len(catalog) == 1
        assert catalog[0].name == "Active Kurti"
        assert len(catalog[0].variants) == 1


# ============================================================================
# Inventory Service Tests (Mocked)
# ============================================================================

class TestInventoryService:
    def test_sellable_stock_calculation(self):
        # sellable = available - reserved
        sellable = InventoryService.calculate_sellable_stock(available_quantity=20, reserved_quantity=5)
        assert sellable == 15

    def test_sellable_stock_rejects_negative_or_excess_reserved(self):
        with pytest.raises(ConstraintViolationError):
            InventoryService.calculate_sellable_stock(available_quantity=-1, reserved_quantity=0)

        with pytest.raises(ConstraintViolationError) as exc_info:
            InventoryService.calculate_sellable_stock(available_quantity=5, reserved_quantity=10)
        assert "Reserved stock (10) exceeds physical available stock (5)" in str(exc_info.value)

    def test_stock_availability_validation(self):
        seller_id = uuid.uuid4()
        var_id = uuid.uuid4()
        initial_data = {
            "inventory": [{
                "id": str(uuid.uuid4()),
                "seller_id": str(seller_id),
                "variant_id": str(var_id),
                "available_quantity": 10,
                "reserved_quantity": 2,
                "low_stock_threshold": 3,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }],
            "product_variants": []
        }
        client = InMemoryMockClient(initial_data)
        service = InventoryService(client)

        # Sellable is 10 - 2 = 8
        assert service.validate_stock_availability(seller_id=seller_id, variant_id=var_id, requested_qty=5) is True
        assert service.validate_stock_availability(seller_id=seller_id, variant_id=var_id, requested_qty=8) is True

        # Requesting 9 fails
        with pytest.raises(InsufficientStockError) as exc_info:
            service.validate_stock_availability(seller_id=seller_id, variant_id=var_id, requested_qty=9)
        assert "Available sellable: 8, requested: 9" in str(exc_info.value)

    def test_inventory_update_enforces_reserved_less_than_available(self):
        seller_id = uuid.uuid4()
        var_id = uuid.uuid4()
        initial_data = {
            "inventory": [{
                "id": str(uuid.uuid4()),
                "seller_id": str(seller_id),
                "variant_id": str(var_id),
                "available_quantity": 10,
                "reserved_quantity": 2,
                "low_stock_threshold": 3,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }],
            "product_variants": []
        }
        client = InMemoryMockClient(initial_data)
        service = InventoryService(client)

        with pytest.raises(ConstraintViolationError):
            service.update_inventory(
                seller_id=seller_id,
                variant_id=var_id,
                data=InventoryUpdateRequest(available_quantity=5, reserved_quantity=8)
            )


# ============================================================================
# Order Service Tests (Mocked)
# ============================================================================

class TestOrderService:
    def test_authoritative_price_calculation_decimal(self):
        seller_id = uuid.uuid4()
        prod_id = uuid.uuid4()
        var_1 = uuid.uuid4()
        var_2 = uuid.uuid4()

        initial_data = {
            "products": [{
                "id": str(prod_id),
                "seller_id": str(seller_id),
                "name": "Designer Kurti",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            }],
            "product_variants": [
                {
                    "id": str(var_1),
                    "seller_id": str(seller_id),
                    "product_id": str(prod_id),
                    "sku": "DK-M",
                    "size": "M",
                    "price": 499.50,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(var_2),
                    "seller_id": str(seller_id),
                    "product_id": str(prod_id),
                    "sku": "DK-L",
                    "size": "L",
                    "price": 549.25,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "inventory": [],
            "orders": [],
            "order_items": []
        }
        client = InMemoryMockClient(initial_data)
        service = OrderService(client)

        items = [
            OrderItemCreateRequest(variant_id=var_1, quantity=2),  # 2 * 499.50 = 999.00
            OrderItemCreateRequest(variant_id=var_2, quantity=1),  # 1 * 549.25 = 549.25
        ]
        total, specs = service.calculate_order_total(seller_id=seller_id, items=items)

        assert total == Decimal("1548.25")
        assert len(specs) == 2
        assert specs[0]["product_name_snapshot"] == "Designer Kurti"
        assert specs[0]["line_total"] == Decimal("999.00")
        assert specs[1]["line_total"] == Decimal("549.25")

    def test_order_status_transitions(self):
        # Valid forward transitions
        assert OrderService.validate_order_status_transition("pending", "confirmed") is True
        assert OrderService.validate_order_status_transition("confirmed", "processing") is True
        assert OrderService.validate_order_status_transition("processing", "shipped") is True
        assert OrderService.validate_order_status_transition("shipped", "delivered") is True
        assert OrderService.validate_order_status_transition("pending", "cancelled") is True

        # Invalid backwards / illegal transitions
        with pytest.raises(InvalidOrderTransitionError):
            OrderService.validate_order_status_transition("cancelled", "shipped")

        with pytest.raises(InvalidOrderTransitionError):
            OrderService.validate_order_status_transition("delivered", "pending")

        with pytest.raises(InvalidOrderTransitionError):
            OrderService.validate_order_status_transition("pending", "delivered")


# ============================================================================
# Payment Service Tests (Mocked)
# ============================================================================

class TestPaymentService:
    def test_calculate_paid_amount_only_counts_verified_payments(self):
        seller_id = uuid.uuid4()
        ord_id = uuid.uuid4()

        initial_data = {
            "orders": [{
                "id": str(ord_id),
                "seller_id": str(seller_id),
                "customer_id": str(uuid.uuid4()),
                "status": "pending",
                "total_amount": 2000.00,
                "currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }],
            "payments": [
                {
                    "id": str(uuid.uuid4()),
                    "seller_id": str(seller_id),
                    "order_id": str(ord_id),
                    "amount": 500.00,
                    "status": "pending",  # Unverified
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "seller_id": str(seller_id),
                    "order_id": str(ord_id),
                    "amount": 750.00,
                    "status": "verified",  # Verified
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "seller_id": str(seller_id),
                    "order_id": str(ord_id),
                    "amount": 200.00,
                    "status": "rejected",  # Rejected
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ]
        }
        client = InMemoryMockClient(initial_data)
        service = PaymentService(client)

        paid = service.calculate_order_paid_amount(seller_id=seller_id, order_id=ord_id)
        assert paid == Decimal("750.00")

        # Outstanding is 2000 - 750 = 1250
        outstanding = service.calculate_outstanding_balance(seller_id=seller_id, order_id=ord_id)
        assert outstanding == Decimal("1250.00")

    def test_find_matching_order_unique_amount(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        ord_1 = uuid.uuid4()
        ord_2 = uuid.uuid4()

        initial_data = {
            "orders": [
                {
                    "id": str(ord_1),
                    "seller_id": str(seller_id),
                    "customer_id": str(cust_id),
                    "status": "pending",
                    "total_amount": 850.00,
                    "currency": "INR",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(ord_2),
                    "seller_id": str(seller_id),
                    "customer_id": str(cust_id),
                    "status": "pending",
                    "total_amount": 1200.00,
                    "currency": "INR",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "payments": []
        }
        client = InMemoryMockClient(initial_data)
        service = PaymentService(client)

        # Exact match for 850 -> matches ord_1
        matched = service.find_matching_order(seller_id=seller_id, customer_id=cust_id, amount=Decimal("850.00"))
        assert matched is not None
        assert str(matched.id) == str(ord_1)

    def test_find_matching_order_ambiguity_raises_error(self):
        seller_id = uuid.uuid4()
        cust_id = uuid.uuid4()
        ord_1 = uuid.uuid4()
        ord_2 = uuid.uuid4()

        initial_data = {
            "orders": [
                {
                    "id": str(ord_1),
                    "seller_id": str(seller_id),
                    "customer_id": str(cust_id),
                    "status": "pending",
                    "total_amount": 500.00,
                    "currency": "INR",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(ord_2),
                    "seller_id": str(seller_id),
                    "customer_id": str(cust_id),
                    "status": "pending",
                    "total_amount": 500.00,
                    "currency": "INR",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "payments": []
        }
        client = InMemoryMockClient(initial_data)
        service = PaymentService(client)

        # Two orders both outstanding 500 -> Ambiguity error
        with pytest.raises(AmbiguousPaymentMatchError) as exc_info:
            service.find_matching_order(seller_id=seller_id, customer_id=cust_id, amount=Decimal("500.00"))
        assert "matches 2 orders" in str(exc_info.value)

    def test_payment_verification_requires_owner_approval(self):
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
        service = PaymentService(client)

        # AI extraction attempting to record payment directly as verified is demoted to pending
        req = PaymentCreateRequest(
            order_id=ord_id,
            amount=Decimal("1000.00"),
            method=PaymentMethod.UPI,
            status=PaymentStatus.VERIFIED
        )
        pay = service.record_payment(seller_id=seller_id, data=req, is_owner_action=False)
        assert pay.status == PaymentStatus.PENDING

        # Updating to verified without owner approval is rejected
        with pytest.raises(ConstraintViolationError):
            service.update_payment_status(
                seller_id=seller_id,
                payment_id=pay.id,
                new_status=PaymentStatus.VERIFIED,
                is_owner_action=False
            )

        # Updating with owner approval succeeds
        verified_pay = service.update_payment_status(
            seller_id=seller_id,
            payment_id=pay.id,
            new_status=PaymentStatus.VERIFIED,
            is_owner_action=True
        )
        assert verified_pay.status == PaymentStatus.VERIFIED

    def test_payment_status_transitions_valid_and_invalid(self):
        assert PaymentService.validate_payment_status_transition("pending", "verification_required") is True
        assert PaymentService.validate_payment_status_transition("pending", "verified") is True
        assert PaymentService.validate_payment_status_transition("verified", "refunded") is True

        # Illegal backwards transition
        with pytest.raises(InvalidPaymentTransitionError):
            PaymentService.validate_payment_status_transition("refunded", "verified")

        with pytest.raises(InvalidPaymentTransitionError):
            PaymentService.validate_payment_status_transition("rejected", "pending")

