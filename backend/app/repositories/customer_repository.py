import logging
from typing import List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.customer import Customer
from backend.app.schemas.customer import CustomerCreateRequest, CustomerUpdateRequest, validate_phone_number
from backend.app.repositories.exceptions import (
    NotFoundError,
    DuplicateRecordError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class CustomerRepository:
    """Data-access repository for the Supabase 'customers' table."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def create_customer(
        self,
        seller_id: Union[str, UUID],
        data: CustomerCreateRequest
    ) -> Customer:
        """
        Creates a new customer record owned by the specified seller.
        Rejects duplicate phone numbers for the same seller.
        """
        sid = self._normalize_id(seller_id)
        # Check if phone already registered for this seller
        existing = self.get_customer_by_phone(seller_id=sid, phone=data.phone)
        if existing:
            raise DuplicateRecordError(f"Customer with phone '{data.phone}' already exists for this seller.")

        payload = {
            "seller_id": sid,
            "phone": data.phone,
            "name": data.name,
            "notes": data.notes,
        }

        try:
            res = (
                self.db.table("customers")
                .insert(payload)
                .execute()
            )
            if not res.data:
                raise DuplicateRecordError("Customer could not be created or already exists.")
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Customer.model_validate(row)
        except Exception as e:
            if isinstance(e, DuplicateRecordError):
                raise
            raise map_supabase_error(e, entity="Customer")

    def get_customer_by_id(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID]
    ) -> Optional[Customer]:
        """Fetches a single customer by ID, strictly scoped to seller_id."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        try:
            res = (
                self.db.table("customers")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", cid)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Customer.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Customer")

    def get_customer_by_phone(
        self,
        seller_id: Union[str, UUID],
        phone: str
    ) -> Optional[Customer]:
        """Finds a customer by phone number, strictly scoped to seller_id, supporting standard international variants."""
        sid = self._normalize_id(seller_id)
        clean_phone = validate_phone_number(phone)

        candidate_phones = [clean_phone]
        if clean_phone.startswith("+"):
            candidate_phones.append(clean_phone[1:])
            if clean_phone.startswith("+91") and len(clean_phone) == 13:
                candidate_phones.append(clean_phone[3:])
        elif len(clean_phone) == 10:
            candidate_phones.append("+91" + clean_phone)
            candidate_phones.append("91" + clean_phone)

        try:
            res = (
                self.db.table("customers")
                .select("*")
                .eq("seller_id", sid)
                .in_("phone", candidate_phones)
                .maybe_single()
                .execute()
            )
            if not res or not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) and res.data else res.data
            if not row or not isinstance(row, dict):
                return None
            return Customer.model_validate(row)
        except Exception as e:
            raise map_supabase_error(e, entity="Customer")

    def list_customers(
        self,
        seller_id: Union[str, UUID],
        limit: int = 50,
        offset: int = 0
    ) -> List[Customer]:
        """Lists customers belonging to the seller with pagination."""
        sid = self._normalize_id(seller_id)
        safe_limit = max(1, min(limit, 100))
        safe_offset = max(0, offset)

        try:
            res = (
                self.db.table("customers")
                .select("*")
                .eq("seller_id", sid)
                .order("created_at", desc=True)
                .range(safe_offset, safe_offset + safe_limit - 1)
                .execute()
            )
            rows = res.data or []
            return [Customer.model_validate(r) for r in rows]
        except Exception as e:
            raise map_supabase_error(e, entity="Customer")

    def update_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        data: CustomerUpdateRequest
    ) -> Optional[Customer]:
        """
        Updates an existing customer belonging to the seller.
        Rejects updating to a phone number that belongs to another customer of the same seller.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        update_dict = {}
        if data.phone is not None:
            # Check phone uniqueness if changing phone
            existing = self.get_customer_by_phone(seller_id=sid, phone=data.phone)
            if existing and str(existing.id) != cid:
                raise DuplicateRecordError(f"Another customer with phone '{data.phone}' already exists.")
            update_dict["phone"] = data.phone
        if data.name is not None:
            update_dict["name"] = data.name
        if data.notes is not None:
            update_dict["notes"] = data.notes

        if not update_dict:
            return self.get_customer_by_id(seller_id=sid, customer_id=cid)

        try:
            res = (
                self.db.table("customers")
                .update(update_dict)
                .eq("seller_id", sid)
                .eq("id", cid)
                .execute()
            )
            if not res.data:
                return None
            row = res.data[0] if isinstance(res.data, list) else res.data
            return Customer.model_validate(row)
        except Exception as e:
            if isinstance(e, DuplicateRecordError):
                raise
            raise map_supabase_error(e, entity="Customer")

    def delete_customer(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID]
    ) -> bool:
        """Deletes a customer belonging to the seller."""
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        try:
            res = (
                self.db.table("customers")
                .delete()
                .eq("seller_id", sid)
                .eq("id", cid)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            raise map_supabase_error(e, entity="Customer")
