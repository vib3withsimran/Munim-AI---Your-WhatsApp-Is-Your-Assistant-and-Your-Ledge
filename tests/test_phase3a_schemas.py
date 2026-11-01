import uuid
from decimal import Decimal
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from backend.app.models.customer import Customer
from backend.app.models.product import Product, ProductVariant
from backend.app.models.inventory import Inventory
from backend.app.models.order import Order, OrderItem
from backend.app.models.payment import Payment

from backend.app.schemas.customer import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    CustomerResponse,
    validate_phone_number,
)
from backend.app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
    ProductVariantResponse,
)
from backend.app.schemas.inventory import (
    InventoryUpdateRequest,
    InventoryResponse,
)
from backend.app.schemas.order import (
    OrderStatus,
    OrderItemCreateRequest,
    OrderItemResponse,
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderResponse,
)
from backend.app.schemas.payment import (
    PaymentStatus,
    PaymentMethod,
    PaymentCreateRequest,
    PaymentStatusUpdateRequest,
    PaymentResponse,
)


# ============================================================================
# Customer Validation Tests
# ============================================================================

class TestCustomerValidation:
    def test_customer_create_valid(self):
        req = CustomerCreateRequest(
            phone="+91 98765-43210",
            name="  Priya Sharma  ",
            notes="Prefers WhatsApp notifications"
        )
        assert req.phone == "+919876543210"
        assert req.name == "Priya Sharma"
        assert req.notes == "Prefers WhatsApp notifications"

    def test_customer_create_missing_phone(self):
        with pytest.raises(ValidationError) as exc_info:
            CustomerCreateRequest.model_validate({"name": "No Phone"})
        assert "phone" in str(exc_info.value)

    def test_customer_create_invalid_phone_format(self):
        invalid_phones = ["12345", "phone12345678", "++919876543210", "1234567890123456789"]
        for p in invalid_phones:
            with pytest.raises(ValidationError):
                CustomerCreateRequest(phone=p)

    def test_customer_rejects_untrusted_seller_id_input(self):
        raw_input = {
            "seller_id": str(uuid.uuid4()),
            "phone": "+919876543210",
            "name": "Trusted Customer"
        }
        with pytest.raises(ValidationError) as exc_info:
            CustomerCreateRequest.model_validate(raw_input)
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_customer_domain_model_valid(self):
        cust_id = uuid.uuid4()
        seller_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        model = Customer(
            id=cust_id,
            seller_id=seller_id,
            phone="+919876543210",
            name="Ramesh",
            notes=None,
            created_at=now
        )
        assert model.id == cust_id
        assert model.seller_id == seller_id

    def test_customer_domain_model_invalid_uuid(self):
        with pytest.raises(ValidationError):
            Customer(
                id="not-a-valid-uuid",
                seller_id=uuid.uuid4(),
                phone="+919876543210",
                created_at=datetime.now(timezone.utc)
            )


# ============================================================================
# Product & Variant Validation Tests
# ============================================================================

class TestProductValidation:
    def test_product_create_valid(self):
        req = ProductCreateRequest(
            name="  Anarkali Kurti  ",
            description="Cotton printed",
            category="Ethnic Wear",
            is_active=True
        )
        assert req.name == "Anarkali Kurti"
        assert req.is_active is True

    def test_product_create_empty_or_whitespace_name(self):
        with pytest.raises(ValidationError):
            ProductCreateRequest(name="")
        with pytest.raises(ValidationError):
            ProductCreateRequest(name="    ")

    def test_product_create_missing_name(self):
        with pytest.raises(ValidationError):
            ProductCreateRequest.model_validate({"category": "Apparel"})

    def test_product_domain_model_valid(self):
        prod_id = uuid.uuid4()
        seller_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        p = Product(
            id=prod_id,
            seller_id=seller_id,
            name="Blue Kurti",
            description=None,
            category="Kurties",
            image_path="uploads/kurti.jpg",
            is_active=True,
            created_at=now
        )
        assert p.id == prod_id
        assert p.is_active is True


class TestProductVariantValidation:
    def test_variant_create_valid(self):
        prod_id = uuid.uuid4()
        req = ProductVariantCreateRequest(
            product_id=prod_id,
            sku="KURTI-BLU-M",
            size="M",
            color="Blue",
            price=Decimal("899.50")
        )
        assert req.product_id == prod_id
        assert req.price == Decimal("899.50")

    def test_variant_rejects_negative_price(self):
        prod_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            ProductVariantCreateRequest(
                product_id=prod_id,
                price=Decimal("-1.00")
            )
        with pytest.raises(ValidationError):
            ProductVariantCreateRequest(
                product_id=prod_id,
                price=Decimal("-0.01")
            )

    def test_variant_rejects_invalid_uuid(self):
        with pytest.raises(ValidationError):
            ProductVariantCreateRequest(
                product_id="invalid-uuid-string",
                price=Decimal("100.00")
            )

    def test_variant_avoids_floating_point_imprecision(self):
        v = ProductVariantCreateRequest(
            product_id=uuid.uuid4(),
            price=Decimal("19.99")
        )
        assert isinstance(v.price, Decimal)
        assert v.price == Decimal("19.99")


# ============================================================================
# Inventory Validation Tests
# ============================================================================

class TestInventoryValidation:
    def test_inventory_update_valid(self):
        req = InventoryUpdateRequest(
            available_quantity=25,
            reserved_quantity=3,
            low_stock_threshold=5
        )
        assert req.available_quantity == 25
        assert req.reserved_quantity == 3
        assert req.low_stock_threshold == 5

    def test_inventory_rejects_negative_available_quantity(self):
        with pytest.raises(ValidationError):
            InventoryUpdateRequest(available_quantity=-1)

    def test_inventory_rejects_negative_reserved_quantity(self):
        with pytest.raises(ValidationError):
            InventoryUpdateRequest(reserved_quantity=-10)

    def test_inventory_rejects_negative_threshold(self):
        with pytest.raises(ValidationError):
            InventoryUpdateRequest(low_stock_threshold=-2)

    def test_inventory_domain_model_valid(self):
        inv_id = uuid.uuid4()
        seller_id = uuid.uuid4()
        variant_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        inv = Inventory(
            id=inv_id,
            seller_id=seller_id,
            variant_id=variant_id,
            available_quantity=50,
            reserved_quantity=2,
            low_stock_threshold=10,
            updated_at=now
        )
        assert inv.variant_id == variant_id
        assert inv.available_quantity == 50


# ============================================================================
# Order & OrderItem Validation Tests
# ============================================================================

class TestOrderValidation:
    def test_order_item_create_valid(self):
        var_id = uuid.uuid4()
        item = OrderItemCreateRequest(variant_id=var_id, quantity=3)
        assert item.variant_id == var_id
        assert item.quantity == 3

    def test_order_item_create_rejects_zero_or_negative_quantity(self):
        var_id = uuid.uuid4()
        with pytest.raises(ValidationError):
            OrderItemCreateRequest(variant_id=var_id, quantity=0)
        with pytest.raises(ValidationError):
            OrderItemCreateRequest(variant_id=var_id, quantity=-2)

    def test_order_item_rejects_invalid_uuid(self):
        with pytest.raises(ValidationError):
            OrderItemCreateRequest(variant_id="bad-uuid", quantity=1)

    def test_order_create_valid(self):
        cust_id = uuid.uuid4()
        var_id = uuid.uuid4()
        req = OrderCreateRequest(
            customer_id=cust_id,
            items=[OrderItemCreateRequest(variant_id=var_id, quantity=2)],
            currency="inr",
            notes="Please pack securely"
        )
        assert req.customer_id == cust_id
        assert req.currency == "INR"
        assert len(req.items) == 1

    def test_order_create_rejects_empty_items(self):
        with pytest.raises(ValidationError):
            OrderCreateRequest(
                customer_id=uuid.uuid4(),
                items=[]
            )

    def test_order_create_rejects_invalid_currency(self):
        with pytest.raises(ValidationError):
            OrderCreateRequest(
                customer_id=uuid.uuid4(),
                items=[OrderItemCreateRequest(variant_id=uuid.uuid4(), quantity=1)],
                currency="TOOLONG"
            )

    def test_order_status_valid_and_invalid(self):
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "completed"]
        for s in valid_statuses:
            status_req = OrderStatusUpdateRequest(status=OrderStatus(s))
            assert status_req.status.value == s

        with pytest.raises(ValidationError):
            OrderStatusUpdateRequest(status="unknown_random_status")

    def test_order_create_rejects_frontend_total_amount(self):
        raw_payload = {
            "customer_id": str(uuid.uuid4()),
            "items": [{"variant_id": str(uuid.uuid4()), "quantity": 1}],
            "total_amount": 5.00  # Attempting to supply untrusted total
        }
        with pytest.raises(ValidationError) as exc_info:
            OrderCreateRequest.model_validate(raw_payload)
        assert "Extra inputs are not permitted" in str(exc_info.value)

    def test_order_item_preserves_snapshots_in_response(self):
        item_resp = OrderItemResponse(
            id=uuid.uuid4(),
            order_id=uuid.uuid4(),
            seller_id=uuid.uuid4(),
            variant_id=uuid.uuid4(),
            quantity=2,
            unit_price=Decimal("499.00"),
            line_total=Decimal("998.00"),
            product_name_snapshot="Pure Cotton Kurti",
            variant_snapshot={"size": "XL", "color": "Red", "sku": "CK-XL-RED"}
        )
        assert item_resp.product_name_snapshot == "Pure Cotton Kurti"
        assert item_resp.variant_snapshot["size"] == "XL"


# ============================================================================
# Payment Validation Tests
# ============================================================================

class TestPaymentValidation:
    def test_payment_create_valid(self):
        ord_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        req = PaymentCreateRequest(
            order_id=ord_id,
            amount=Decimal("1500.00"),
            method=PaymentMethod.UPI,
            status=PaymentStatus.PENDING,
            transaction_reference="UPI/2026/12345678",
            paid_at=now
        )
        assert req.order_id == ord_id
        assert req.amount == Decimal("1500.00")
        assert req.method == PaymentMethod.UPI
        assert req.status == PaymentStatus.PENDING

    def test_payment_create_rejects_negative_amount(self):
        with pytest.raises(ValidationError):
            PaymentCreateRequest(
                amount=Decimal("-100.00")
            )

    def test_payment_status_valid_and_invalid(self):
        valid_statuses = ["pending", "verification_required", "verified", "rejected", "refunded", "completed"]
        for s in valid_statuses:
            status_req = PaymentStatusUpdateRequest(status=PaymentStatus(s))
            assert status_req.status.value == s

        with pytest.raises(ValidationError):
            PaymentStatusUpdateRequest(status="auto_verified_by_ai")

    def test_nullable_order_association_behavior(self):
        # 1. Nullable when omitted (defaults to None)
        req_omitted = PaymentCreateRequest(amount=Decimal("200.00"))
        assert req_omitted.order_id is None

        # 2. Nullable when explicitly None
        req_none = PaymentCreateRequest(amount=Decimal("200.00"), order_id=None)
        assert req_none.order_id is None

        # 3. Valid when valid UUID provided
        ord_uuid = uuid.uuid4()
        req_with_order = PaymentCreateRequest(amount=Decimal("200.00"), order_id=ord_uuid)
        assert req_with_order.order_id == ord_uuid

        # 4. Invalid when malformed UUID string provided
        with pytest.raises(ValidationError):
            PaymentCreateRequest(amount=Decimal("200.00"), order_id="not-a-valid-uuid")

    def test_payment_response_from_database_row(self):
        pay_id = uuid.uuid4()
        seller_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        resp = PaymentResponse(
            id=pay_id,
            seller_id=seller_id,
            order_id=None,  # Unlinked payment
            amount=Decimal("750.50"),
            method="upi",
            status=PaymentStatus.VERIFIED,
            transaction_reference="TXN987654",
            paid_at=now,
            created_at=now
        )
        assert resp.id == pay_id
        assert resp.order_id is None
        assert resp.status == PaymentStatus.VERIFIED
