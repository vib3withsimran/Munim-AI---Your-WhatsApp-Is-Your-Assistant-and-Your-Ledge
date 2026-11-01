import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID
from supabase import Client

from backend.app.models.order import Order, OrderItem
from backend.app.schemas.order import (
    OrderCreateRequest,
    OrderItemCreateRequest,
    OrderStatus,
)
from backend.app.repositories.order_repository import OrderRepository
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.exceptions import (
    NotFoundError,
    ForeignKeyViolationError,
    PermissionDeniedError,
    ConstraintViolationError,
    RepositoryError,
)
from backend.app.services.inventory_service import InventoryService
from backend.app.services.exceptions import (
    BusinessRuleError,
    InsufficientStockError,
    InvalidOrderTransitionError,
)

logger = logging.getLogger(__name__)


# Allowed order status transitions
VALID_ORDER_TRANSITIONS: Dict[str, List[str]] = {
    "pending": ["confirmed", "processing", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped", "completed", "cancelled"],
    "shipped": ["delivered", "completed", "cancelled"],
    "delivered": [],  # Terminal
    "completed": [],  # Terminal
    "cancelled": [],  # Terminal
}


class OrderService:
    """
    Business logic service for orders, server-authoritative pricing,
    and lifecycle status transitions.
    """

    def __init__(self, db: Client):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.product_repo = ProductRepository(db)
        self.inventory_service = InventoryService(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_order(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> Optional[Order]:
        """Fetches order by ID with strict seller ownership verification."""
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)
        return self.order_repo.get_order_by_id(seller_id=sid, order_id=oid)

    def list_orders(
        self,
        seller_id: Union[str, UUID],
        status: Optional[str] = None,
        customer_id: Optional[Union[str, UUID]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Lists orders owned by seller with optional filters."""
        sid = self._normalize_id(seller_id)
        return self.order_repo.list_orders(
            seller_id=sid,
            status=status,
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )

    def get_customer_orders(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Retrieves orders for a customer owned by this seller."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)
        return self.order_repo.get_orders_by_customer(seller_id=sid, customer_id=cid, limit=limit, offset=offset)

    def get_order_items(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> List[OrderItem]:
        """Retrieves all line items for an order owned by this seller."""
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        order = self.get_order(seller_id=sid, order_id=oid)
        if not order:
            raise NotFoundError(f"Order '{oid}' not found or not owned by this seller.")

        return self.order_repo.get_order_items(seller_id=sid, order_id=oid)

    # =========================================================================
    # Server-Authoritative Pricing & Snapshots
    # =========================================================================

    def calculate_order_total(
        self,
        seller_id: Union[str, UUID],
        items: List[OrderItemCreateRequest]
    ) -> Tuple[Decimal, List[Dict[str, Any]]]:
        """
        Calculates authoritative line totals and total order amount.
        - Fetches canonical prices directly from product_variants.
        - Fetches product name snapshot from products.
        - Preserves variant size, color, and SKU in snapshot JSONB.
        - Never trusts frontend prices or totals.
        """
        sid = self._normalize_id(seller_id)
        total_amount = Decimal("0.00")
        line_specs: List[Dict[str, Any]] = []

        for it in items:
            vid = self._normalize_id(it.variant_id)
            variant = self.product_repo.get_variant_by_id(seller_id=sid, variant_id=vid)
            if not variant:
                raise ForeignKeyViolationError(f"Variant '{vid}' not found or not owned by this seller.")

            parent_product = self.product_repo.get_product_by_id(seller_id=sid, product_id=variant.product_id)
            product_name = parent_product.name if parent_product else "Product"

            unit_price = Decimal(str(variant.price))
            quantity = it.quantity
            line_total = round(unit_price * Decimal(quantity), 2)
            total_amount += line_total

            variant_snapshot = {
                "sku": variant.sku,
                "size": variant.size,
                "color": variant.color,
            }

            line_specs.append({
                "variant_id": vid,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "product_name_snapshot": product_name,
                "variant_snapshot": variant_snapshot,
            })

        return round(total_amount, 2), line_specs

    def validate_order_request(
        self,
        seller_id: Union[str, UUID],
        data: OrderCreateRequest
    ) -> Dict[str, Any]:
        """
        Validates customer, items, authoritative pricing, and stock availability.
        Prepares manifest for the atomic order placement PostgreSQL transaction.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(data.customer_id)

        # 1. Verify customer ownership
        customer = self.customer_repo.get_customer_by_id(seller_id=sid, customer_id=cid)
        if not customer:
            raise NotFoundError(f"Customer '{cid}' not found or not owned by this seller.")

        # 2. Authoritative price & snapshot computation
        total_amount, line_specs = self.calculate_order_total(seller_id=sid, items=data.items)

        # 3. Verify stock availability for each variant
        for line in line_specs:
            self.inventory_service.validate_stock_availability(
                seller_id=sid,
                variant_id=line["variant_id"],
                requested_qty=line["quantity"]
            )

        return {
            "seller_id": sid,
            "customer_id": cid,
            "status": OrderStatus.PENDING.value,
            "total_amount": total_amount,
            "currency": data.currency,
            "notes": data.notes,
            "items": line_specs,
        }

    # =========================================================================
    # Order Status Transitions
    # =========================================================================

    @staticmethod
    def validate_order_status_transition(current_status: str, target_status: str) -> bool:
        """
        Validates whether target_status is a valid progression from current_status.
        Raises InvalidOrderTransitionError if transition is illegal.
        """
        curr = current_status.lower().strip()
        tgt = target_status.lower().strip()

        if curr == tgt:
            return True  # Idempotent status update

        allowed_targets = VALID_ORDER_TRANSITIONS.get(curr, [])
        if tgt not in allowed_targets:
            raise InvalidOrderTransitionError(from_status=curr, to_status=tgt)
        return True

    def update_order_status(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID],
        new_status: Union[str, OrderStatus]
    ) -> Order:
        """
        Validates lifecycle transition and updates the order status.
        """
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)
        target = new_status.value if isinstance(new_status, OrderStatus) else str(new_status)

        order = self.get_order(seller_id=sid, order_id=oid)
        if not order:
            raise NotFoundError(f"Order '{oid}' not found or not owned by this seller.")

        # Enforce transition rules
        self.validate_order_status_transition(current_status=order.status, target_status=target)

        update_dict = {
            "status": target,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            res = (
                self.db.table("orders")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("id", oid)
                .execute()
            )
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            return Order.model_validate(row)
        except Exception as e:
            if isinstance(e, InvalidOrderTransitionError):
                raise
            raise RuntimeError(f"Failed to update order status: {e}")

    # =========================================================================
    # Error Mapping for PostgreSQL RPCs
    # =========================================================================

    def _map_rpc_error(self, e: Exception) -> Exception:
        """
        Maps PostgreSQL errors raised during RPC transactions into typed domain exceptions.
        """
        if isinstance(e, (InsufficientStockError, NotFoundError, PermissionDeniedError, InvalidOrderTransitionError, BusinessRuleError, ConstraintViolationError)):
            return e

        msg = str(e)
        code = getattr(e, "code", None)
        if not code and hasattr(e, "args") and e.args and isinstance(e.args[0], dict):
            code = e.args[0].get("code")

        if hasattr(e, "message") and e.message:
            msg = e.message
        elif hasattr(e, "args") and e.args and isinstance(e.args[0], dict) and "message" in e.args[0]:
            msg = e.args[0]["message"]

        if "INSUFFICIENT_STOCK" in msg or code == "P0001":
            return InsufficientStockError(msg)
        if "NOT_FOUND" in msg or code == "P0002":
            return NotFoundError(msg)
        if "PERMISSION_DENIED" in msg or "UNAUTHENTICATED" in msg or code == "42501":
            return PermissionDeniedError(msg)
        if "INVALID_ORDER_TRANSITION" in msg:
            return InvalidOrderTransitionError(message=msg)
        if any(token in msg for token in ("INVALID_QUANTITY", "DUPLICATE_ITEM", "INVALID_INPUT", "INACTIVE_PRODUCT")):
            return BusinessRuleError(msg)
        if "CONSTRAINT_VIOLATION" in msg or "chk_inventory_quantities_valid" in msg or code == "23514":
            return ConstraintViolationError(msg)
        if "foreign key constraint" in msg or code == "23503":
            return ForeignKeyViolationError(f"Foreign key constraint violated: {msg}")

        return RepositoryError(f"Transactional operation failed: {msg}", details=msg)

    # =========================================================================
    # Atomic PostgreSQL Transactional RPC Wrappers (Phase 3D)
    # =========================================================================

    def create_order_with_reservation(
        self,
        seller_id: Union[str, UUID],
        data: OrderCreateRequest
    ) -> Order:
        """
        Executes atomic order placement and inventory reservation inside a single PostgreSQL transaction.
        - Locks relevant inventory rows in consistent ascending order to prevent deadlocks.
        - Verifies customer ownership, variant ownership, and product active status.
        - Verifies sellable stock (available_quantity - reserved_quantity >= requested).
        - Authoritatively calculates total amount using canonical variant prices.
        - Inserts into 'orders' and 'order_items' with snapshots.
        - Increments reserved_quantity in 'inventory'.
        - Rolls back all changes if any validation or stock check fails.
        """
        sid = self._normalize_id(seller_id)
        items_payload = [
            {"variant_id": str(it.variant_id), "quantity": it.quantity}
            for it in data.items
        ]

        params = {
            "p_customer_id": str(data.customer_id),
            "p_items": items_payload,
            "p_currency": data.currency,
            "p_notes": data.notes,
            "p_seller_id": sid,
        }

        try:
            res = self.db.rpc("create_order_with_reservation_rpc", params).execute()
            order_dict = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not order_dict:
                raise RepositoryError("create_order_with_reservation_rpc returned empty response.")
            return Order.model_validate(order_dict)
        except Exception as e:
            raise self._map_rpc_error(e)

    def fulfill_order(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID],
        target_status: str = "completed"
    ) -> Order:
        """
        Executes atomic order fulfillment inside a single PostgreSQL transaction.
        - Verifies seller ownership and checks order is in eligible status (pending/confirmed/processing).
        - Locks order and inventory rows in consistent order.
        - Atomically decrements physical stock (available_quantity -= qty) and releases reserved stock (reserved_quantity -= qty).
        - Updates order status to target_status (completed/shipped).
        - Rejects duplicate fulfillment and rolls back completely on any failure.
        - Partial fulfillment is explicitly rejected.
        """
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        params = {
            "p_order_id": oid,
            "p_seller_id": sid,
            "p_target_status": target_status,
        }

        try:
            res = self.db.rpc("fulfill_order_rpc", params).execute()
            order_dict = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not order_dict:
                raise RepositoryError("fulfill_order_rpc returned empty response.")
            return Order.model_validate(order_dict)
        except Exception as e:
            raise self._map_rpc_error(e)

    def cancel_order(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> Order:
        """
        Executes atomic order cancellation inside a single PostgreSQL transaction.
        - Verifies seller ownership and confirms order can be cancelled (cannot cancel if already fulfilled or cancelled).
        - Locks order and inventory rows.
        - Decrements reserved_quantity -= qty exactly once (physical available_quantity remains untouched).
        - Updates order status to 'cancelled'.
        - Prevents double stock release and preserves historical order items.
        - Rolls back all changes if any operation fails.
        """
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        params = {
            "p_order_id": oid,
            "p_seller_id": sid,
        }

        try:
            res = self.db.rpc("cancel_order_rpc", params).execute()
            order_dict = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not order_dict:
                raise RepositoryError("cancel_order_rpc returned empty response.")
            return Order.model_validate(order_dict)
        except Exception as e:
            raise self._map_rpc_error(e)


