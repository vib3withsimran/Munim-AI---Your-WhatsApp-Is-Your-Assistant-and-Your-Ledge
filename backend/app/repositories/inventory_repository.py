import logging
from datetime import datetime, timezone
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.inventory import Inventory
from backend.app.schemas.inventory import InventoryUpdateRequest
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class InventoryRepository:
    """Data-access repository for the Supabase 'inventory' table."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_inventory_by_variant(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID]
    ) -> Optional[Inventory]:
        """Fetches the inventory record for a specific variant owned by seller_id."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        try:
            res = (
                self.db.table("inventory")
                .select("*")
                .eq("seller_id", sid)
                .eq("variant_id", vid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Inventory.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Inventory")

    def list_inventory(
        self,
        seller_id: Union[str, UUID],
        low_stock_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Inventory]:
        """Lists inventory records owned by the seller with optional low-stock filter and pagination."""
        sid = self._normalize_id(seller_id)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            query = (
                self.db.table("inventory")
                .select("*")
                .eq("seller_id", sid)
            )

            res = (
                query
                .order("updated_at", desc=True)
                .range(safe_offset, safe_offset + safe_limit - 1)
                .execute()
            )
            rows = res.data or []
            models = [Inventory.model_validate(r) for r in rows]

            if low_stock_only:
                models = [inv for inv in models if inv.available_quantity <= inv.low_stock_threshold]

            return models
        except Exception as e:
            raise map_supabase_error(e, entity="Inventory")

    def create_inventory(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        available_quantity: int = 0,
        reserved_quantity: int = 0,
        low_stock_threshold: int = 5,
    ) -> Inventory:
        """Inserts an initial inventory record for a variant."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)
        payload = {
            "seller_id": sid,
            "variant_id": vid,
            "available_quantity": available_quantity,
            "reserved_quantity": reserved_quantity,
            "low_stock_threshold": low_stock_threshold,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            res = (
                self.db.table("inventory")
                .insert(payload)
                .execute()
            )
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Inventory.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Inventory")

    def update_inventory(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        data: InventoryUpdateRequest
    ) -> Optional[Inventory]:
        """Updates stock quantities or threshold for a variant. Enforces non-negative bounds."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        # Validate non-negative quantities
        if data.available_quantity is not None and data.available_quantity < 0:
            raise ConstraintViolationError("Available quantity cannot be negative")
        if data.reserved_quantity is not None and data.reserved_quantity < 0:
            raise ConstraintViolationError("Reserved quantity cannot be negative")
        if data.low_stock_threshold is not None and data.low_stock_threshold < 0:
            raise ConstraintViolationError("Low-stock threshold cannot be negative")

        update_dict = {}
        if data.available_quantity is not None:
            update_dict["available_quantity"] = data.available_quantity
        if data.reserved_quantity is not None:
            update_dict["reserved_quantity"] = data.reserved_quantity
        if data.low_stock_threshold is not None:
            update_dict["low_stock_threshold"] = data.low_stock_threshold

        if not update_dict:
            return self.get_inventory_by_variant(seller_id=sid, variant_id=vid)

        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

        try:
            res = (
                self.db.table("inventory")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("variant_id", vid)
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Inventory.model_validate(row)
        except Exception as e:
            if isinstance(e, ConstraintViolationError):
                raise
            raise map_supabase_error(e, entity="Inventory")
