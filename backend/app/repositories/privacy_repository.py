import logging
from typing import Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.privacy import PrivacySetting

logger = logging.getLogger(__name__)


class PrivacyRepository:
    """Repository for managing customer privacy settings in Supabase ('privacy_settings' table)."""

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_privacy_status(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
    ) -> bool:
        """
        Returns True if customer has privacy mode enabled (#private) for this seller.
        Returns False by default if no setting exists or on error.
        """
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
            if isinstance(row, dict):
                return bool(row.get("is_private", False))
            return False
        except Exception as e:
            logger.warning(f"Error querying privacy_settings for seller {sid}, customer {cid}: {e}")
            return False

    def set_privacy_status(
        self,
        seller_id: Union[str, UUID],
        customer_id: Union[str, UUID],
        is_private: bool,
    ) -> bool:
        """
        Upserts the privacy setting for (seller_id, customer_id).
        Returns True on success.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id)

        try:
            # Check existing row
            existing = (
                self.db.table("privacy_settings")
                .select("id")
                .eq("seller_id", sid)
                .eq("customer_id", cid)
                .maybe_single()
                .execute()
            )
            row = existing.data[0] if (existing and isinstance(existing.data, list) and existing.data) else (existing.data if existing else None)

            if row and isinstance(row, dict) and "id" in row:
                self.db.table("privacy_settings").update({
                    "is_private": is_private,
                }).eq("id", row["id"]).execute()
            else:
                self.db.table("privacy_settings").insert({
                    "seller_id": sid,
                    "customer_id": cid,
                    "is_private": is_private,
                }).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to persist privacy setting for seller {sid}, customer {cid}: {e}")
            return False

