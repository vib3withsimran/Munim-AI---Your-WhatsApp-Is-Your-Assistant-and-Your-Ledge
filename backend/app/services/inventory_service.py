import logging
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID
from supabase import Client

from backend.app.models.inventory import Inventory
from backend.app.schemas.inventory import InventoryUpdateRequest
from backend.app.repositories.inventory_repository import InventoryRepository
from backend.app.repositories.product_repository import ProductRepository
from backend.app.repositories.exceptions import NotFoundError, ConstraintViolationError
from backend.app.services.exceptions import InsufficientStockError

logger = logging.getLogger(__name__)


class InventoryService:
    """
    Business logic service for stock levels and sellable inventory calculations.

    Inventory Definitions:
    - available_quantity: Physical stock currently on hand in warehouse/store.
    - reserved_quantity: Stock committed to active/unfulfilled orders.
    - sellable stock: available_quantity - reserved_quantity.
    """

    def __init__(self, db: Client):
        self.db = db
        self.inventory_repo = InventoryRepository(db)
        self.product_repo = ProductRepository(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    @staticmethod
    def calculate_sellable_stock(available_quantity: int, reserved_quantity: int) -> int:
        """
        Calculates net sellable stock: available_quantity - reserved_quantity.
        Enforces non-negative result.
        """
        if available_quantity < 0 or reserved_quantity < 0:
            raise ConstraintViolationError("Stock quantities cannot be negative.")
        if reserved_quantity > available_quantity:
            raise ConstraintViolationError(
                f"Data inconsistency: Reserved stock ({reserved_quantity}) exceeds physical available stock ({available_quantity})."
            )
        return available_quantity - reserved_quantity

    def get_inventory(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID]
    ) -> Optional[Inventory]:
        """Fetches the inventory record for a specific variant owned by the seller."""
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)
        return self.inventory_repo.get_inventory_by_variant(seller_id=sid, variant_id=vid)

    def list_inventory(
        self,
        seller_id: Union[str, UUID],
        low_stock_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Inventory]:
        """Lists inventory records owned by the seller."""
        sid = self._normalize_id(seller_id)
        return self.inventory_repo.list_inventory(
            seller_id=sid,
            low_stock_only=low_stock_only,
            limit=limit,
            offset=offset
        )

    def get_low_stock_products(
        self,
        seller_id: Union[str, UUID]
    ) -> List[Inventory]:
        """Returns inventory items where available_quantity <= low_stock_threshold."""
        return self.list_inventory(seller_id=seller_id, low_stock_only=True, limit=100)

    def update_inventory(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        data: InventoryUpdateRequest
    ) -> Inventory:
        """
        Updates stock quantities or threshold.
        Enforces business rule: reserved_quantity cannot exceed available physical stock.
        """
        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        current = self.get_inventory(seller_id=sid, variant_id=vid)
        if not current:
            # Check if variant exists
            variant = self.product_repo.get_variant_by_id(seller_id=sid, variant_id=vid)
            if not variant:
                raise NotFoundError(f"Variant '{vid}' does not exist or is not owned by this seller.")
            # Default baselines if new record
            curr_avail = 0
            curr_res = 0
        else:
            curr_avail = current.available_quantity
            curr_res = current.reserved_quantity

        new_avail = data.available_quantity if data.available_quantity is not None else curr_avail
        new_res = data.reserved_quantity if data.reserved_quantity is not None else curr_res

        if new_avail < 0 or new_res < 0:
            raise ConstraintViolationError("Stock quantities cannot be negative.")

        if new_res > new_avail:
            raise ConstraintViolationError(
                f"Reserved quantity ({new_res}) cannot exceed available physical stock ({new_avail})."
            )

        updated = self.inventory_repo.update_inventory(seller_id=sid, variant_id=vid, data=data)
        if not updated:
            raise NotFoundError(f"Inventory record for variant '{vid}' could not be updated.")
        return updated

    # =========================================================================
    # Transactional Preparation Interfaces (Phase 4 Transaction Support)
    # =========================================================================

    def validate_stock_availability(
        self,
        seller_id: Union[str, UUID],
        variant_id: Union[str, UUID],
        requested_qty: int
    ) -> bool:
        """
        Verifies whether sellable stock is sufficient for requested order quantity.
        Does NOT perform deduction (reservation must occur atomically in PostgreSQL RPC).
        """
        if requested_qty < 1:
            raise ConstraintViolationError("Requested quantity must be at least 1.")

        sid = self._normalize_id(seller_id)
        vid = self._normalize_id(variant_id)

        inv = self.get_inventory(seller_id=sid, variant_id=vid)
        if not inv:
            raise NotFoundError(f"No inventory record found for variant '{vid}'.")

        sellable = self.calculate_sellable_stock(inv.available_quantity, inv.reserved_quantity)
        if sellable < requested_qty:
            raise InsufficientStockError(
                f"Insufficient sellable stock for variant '{vid}'. Available sellable: {sellable}, requested: {requested_qty}."
            )
        return True

    def prepare_reservation_plan(
        self,
        seller_id: Union[str, UUID],
        items: List[Tuple[Union[str, UUID], int]]
    ) -> Dict[str, any]:
        """
        Validates all items for stock availability and prepares the reservation payload.
        Ready for the atomic PostgreSQL transaction RPC.
        """
        plan = []
        for vid, qty in items:
            self.validate_stock_availability(seller_id=seller_id, variant_id=vid, requested_qty=qty)
            plan.append({"variant_id": str(vid), "quantity": qty})
        return {"seller_id": str(seller_id), "reservations": plan}

