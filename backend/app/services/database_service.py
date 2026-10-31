
import logging
from typing import Any

from backend.app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


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
