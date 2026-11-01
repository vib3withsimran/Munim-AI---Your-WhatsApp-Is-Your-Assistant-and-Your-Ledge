import logging
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.customer import Customer
from backend.app.schemas.customer import (
    CustomerCreateRequest,
    CustomerUpdateRequest,
    validate_phone_number,
)
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.order_repository import OrderRepository
from backend.app.repositories.exceptions import NotFoundError, DuplicateRecordError
from backend.app.services.exceptions import BusinessRuleError

logger = logging.getLogger(__name__)


class CustomerService:
    """Business logic service for customer lifecycle, privacy, and integrity."""

    def __init__(self, db: Client):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.order_repo = OrderRepository(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def create_customer(
        self,
        seller_id: Union[str, UUID],
        data: CustomerCreateRequest
    ) -> Customer:
        """
        Creates a new customer record.
        Enforces normalized phone format and prevents duplicates within the same seller.
        """
        sid = self._normalize_id(seller_id)
        clean_phone = validate_phone_number(data.phone)

        # Check existing customer for this seller
        existing = self.customer_repo.get_customer_by_phone(seller_id=sid, phone=clean_phone)
        if existing:
            raise DuplicateRecordError(f"Customer with phone '{clean_phone}' already exists for this seller.")

        # Re-construct request with sanitized phone
        sanitized_req = CustomerCreateRequest(
            phone=clean_phone,
            name=data.name,
            notes=data.notes
        )
        return self.customer_repo.create_customer(seller_id=sid, data=sanitized_req)

    def get_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID]
    ) -> Optional[Customer]:
        """Retrieves customer by ID, strictly enforcing seller ownership."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)
        return self.customer_repo.get_customer_by_id(seller_id=sid, customer_id=cid)

    def get_customer_by_phone(
        self,
        seller_id: Union[str, UUID],
        phone: str
    ) -> Optional[Customer]:
        """Finds customer by normalized phone number for the given seller."""
        sid = self._normalize_id(seller_id)
        clean_phone = validate_phone_number(phone)
        return self.customer_repo.get_customer_by_phone(seller_id=sid, phone=clean_phone)

    def list_customers(
        self,
        seller_id: Union[str, UUID],
        limit: int = 50,
        offset: int = 0
    ) -> List[Customer]:
        """Lists customers belonging to the current seller with pagination."""
        sid = self._normalize_id(seller_id)
        return self.customer_repo.list_customers(seller_id=sid, limit=limit, offset=offset)

    def update_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        data: CustomerUpdateRequest
    ) -> Customer:
        """Updates customer details after verifying seller ownership and phone collision checks."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        existing = self.get_customer(seller_id=sid, customer_id=cid)
        if not existing:
            raise NotFoundError(f"Customer '{cid}' not found or not owned by this seller.")

        updated = self.customer_repo.update_customer(seller_id=sid, customer_id=cid, data=data)
        if not updated:
            raise NotFoundError(f"Customer '{cid}' update failed.")
        return updated

    def archive_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID]
    ) -> bool:
        """
        Safely archives or removes customer without corrupting historical order records.
        If the customer has placed orders, marks customer notes as [ARCHIVED] to preserve order FK integrity.
        If the customer has no orders, safely removes the record.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        customer = self.get_customer(seller_id=sid, customer_id=cid)
        if not customer:
            raise NotFoundError(f"Customer '{cid}' not found or not owned by this seller.")

        orders = self.order_repo.get_orders_by_customer(seller_id=sid, customer_id=cid, limit=1)
        if orders:
            # Customer has active historical orders; preserve FK integrity and mark archived
            archived_notes = f"[ARCHIVED] {customer.notes or ''}".strip()
            self.customer_repo.update_customer(
                seller_id=sid,
                customer_id=cid,
                data=CustomerUpdateRequest(notes=archived_notes)
            )
            return True

        # Safe to hard-delete if no orders exist
        return self.customer_repo.delete_customer(seller_id=sid, customer_id=cid)

    # =========================================================================
    # Privacy Settings
    # =========================================================================

    def is_customer_private(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID]
    ) -> bool:
        """Checks if customer has privacy mode enabled in the privacy_settings table."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        try:
            res = (
                self.db.table("privacy_settings")
                .select("is_private")
                .eq("seller_id", sid)
                .eq("customer_id", cid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return False
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            return bool(row.get("is_private", False)) if isinstance(row, dict) else False
        except Exception:
            return False

    def set_customer_privacy(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        is_private: bool
    ) -> bool:
        """Sets customer privacy setting in Supabase."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        customer = self.get_customer(seller_id=sid, customer_id=cid)
        if not customer:
            raise NotFoundError(f"Customer '{cid}' not found.")

        payload = {
            "seller_id": sid,
            "customer_id": cid,
            "is_private": is_private,
        }
        try:
            res = (
                self.db.table("privacy_settings")
                .upsert(payload, on_conflict="seller_id,customer_id")
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.warning(f"Failed to update customer privacy: {e}")
            return False

