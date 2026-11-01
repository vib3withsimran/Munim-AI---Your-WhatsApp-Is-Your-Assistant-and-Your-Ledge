import logging
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.order import Order, OrderItem
from backend.app.repositories.exceptions import (
    NotFoundError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class OrderRepository:
    """Data-access repository for 'orders' and 'order_items' tables."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_order_by_id(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> Optional[Order]:
        """Fetches a single order by ID, strictly scoped to seller_id."""
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        try:
            res = (
                self.db.table("orders")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", oid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Order.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Order")

    def list_orders(
        self,
        seller_id: Union[str, UUID],
        status: Optional[str] = None,
        customer_id: Optional[Union[str, UUID]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Lists orders owned by seller with optional status and customer filters and pagination."""
        sid = self._normalize_id(seller_id)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            query = (
                self.db.table("orders")
                .select("*")
                .eq("seller_id", sid)
            )

            if status is not None:
                query = query.eq("status", status.lower().strip())
            if customer_id is not None:
                query = query.eq("customer_id", self._normalize_id(customer_id))

            res = (
                query
                .order("created_at", desc=True)
                .range(safe_offset, safe_offset + safe_limit - 1)
                .execute()
            )
            rows = res.data or []
            return [Order.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="Order")

    def get_order_items(
        self,
        seller_id: Union[str, UUID],
        order_id: Union[str, UUID]
    ) -> List[OrderItem]:
        """Fetches all line items belonging to an order owned by seller_id."""
        sid = self._normalize_id(seller_id)
        oid = self._normalize_id(order_id)

        try:
            res = (
                self.db.table("order_items")
                .select("*")
                .eq("seller_id", sid)
                .eq("order_id", oid)
                .execute()
            )
            rows = res.data or []
            return [OrderItem.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="OrderItem")

    def get_orders_by_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Convenience method to retrieve orders for a specific customer."""
        return self.list_orders(
            seller_id=seller_id,
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )
