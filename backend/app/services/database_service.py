
import logging
from typing import Any, Optional

from backend.app.core.supabase_client import get_supabase_client
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_active_seller_uuid: Optional[str] = None

def get_active_seller_id() -> str:
    """
    Resolves the active seller's UUID for database foreign-key operations.
    1. Looks up 'profiles' where phone == OWNER_WHATSAPP_NUMBER.
    2. Fallback to the first existing profile in the table.
    3. Fallback to a valid default UUID format ("00000000-0000-0000-0000-000000000001").
    """
    global _active_seller_uuid
    if _active_seller_uuid:
        return _active_seller_uuid

    try:
        supabase = get_supabase_client()
        owner_phone = settings.OWNER_WHATSAPP_NUMBER.replace("+", "").strip()
        if owner_phone:
            res = supabase.table("profiles").select("id").eq("phone", owner_phone).limit(1).execute()
            if res.data and len(res.data) > 0:
                _active_seller_uuid = str(res.data[0]["id"])
                return _active_seller_uuid

        # Try any registered profile in DB
        res_all = supabase.table("profiles").select("id").limit(1).execute()
        if res_all.data and len(res_all.data) > 0:
            _active_seller_uuid = str(res_all.data[0]["id"])
            return _active_seller_uuid
    except Exception as e:
        logger.warning(f"Could not resolve seller UUID from Supabase profiles: {e}")

    _active_seller_uuid = "00000000-0000-0000-0000-000000000001"
    return _active_seller_uuid


def _validate_seller_id(seller_id: str) -> None:
    """Ensure every database operation has a seller context."""
    if not seller_id or not seller_id.strip():
        raise ValueError("seller_id is required")


def get_customer_by_phone(
    seller_id: str,
    phone: str
) -> dict[str, Any] | None:
    """Find a customer belonging to a specific seller."""
    _validate_seller_id(seller_id)

    if not phone:
        raise ValueError("Customer phone is required")

    supabase = get_supabase_client()

    response = (
        supabase.table("customers")
        .select("*")
        .eq("seller_id", seller_id)
        .eq("phone", phone)
        .maybe_single()
        .execute()
    )

    return response.data


def create_customer(
    seller_id: str,
    phone: str,
    name: str | None = None,
    notes: str | None = None
) -> dict[str, Any]:
    """Create a customer, or update their name/notes if they already exist."""
    _validate_seller_id(seller_id)

    if not phone:
        raise ValueError("Customer phone is required")

    supabase = get_supabase_client()

    customer_data = {
        "seller_id": seller_id,
        "phone": phone,
        "name": name,
        "notes": notes,
    }

    response = (
        supabase.table("customers")
        .upsert(
            customer_data,
            on_conflict="seller_id,phone"
        )
        .execute()
    )

    if not response.data:
        raise RuntimeError("Customer could not be created or updated")

    return response.data[0]


def get_catalog(seller_id: str) -> list[dict[str, Any]]:
    """Retrieve active products belonging to a specific seller."""
    _validate_seller_id(seller_id)

    supabase = get_supabase_client()

    response = (
        supabase.table("products")
        .select("*")
        .eq("seller_id", seller_id)
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    return response.data or []
