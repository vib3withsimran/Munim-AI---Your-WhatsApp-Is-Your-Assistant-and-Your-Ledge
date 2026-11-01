import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.models.media import MediaFile
from backend.app.repositories.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    RepositoryError,
    map_supabase_error,
)

logger = logging.getLogger(__name__)


class MediaRepository:
    """
    Data access repository for 'media_files' table in Supabase.
    Strictly enforces seller-scoping on all queries and mutations.
    """

    def __init__(self, db: Client):
        self.db = db

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def create_media_file(
        self,
        seller_id: Union[str, UUID],
        storage_bucket: str,
        storage_path: str,
        media_type: str,
        purpose: Optional[str] = None,
        customer_id: Optional[Union[str, UUID]] = None,
        processing_status: str = "uploaded",
        media_id: Optional[Union[str, UUID]] = None,
    ) -> MediaFile:
        """
        Inserts a new media record scoped to seller_id.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id) if customer_id else None

        insert_payload: Dict[str, Any] = {
            "seller_id": sid,
            "storage_bucket": storage_bucket,
            "storage_path": storage_path,
            "media_type": media_type,
            "purpose": purpose,
            "customer_id": cid,
            "processing_status": processing_status,
        }
        if media_id:
            insert_payload["id"] = self._normalize_id(media_id)

        try:
            res = self.db.table("media_files").insert(insert_payload).execute()
            if not res.data:
                raise RepositoryError("Failed to insert media_files record: empty response from database.")
            return MediaFile.model_validate(res.data[0])
        except Exception as e:
            map_supabase_error(e, context=f"create_media_file(seller_id={sid})")

    def get_media_by_id(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID]
    ) -> Optional[MediaFile]:
        """
        Retrieves a media record by ID with seller-ownership check.
        Returns None if not found or owned by a different seller.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        try:
            res = (
                self.db.table("media_files")
                .select("*")
                .eq("seller_id", sid)
                .eq("id", mid)
                .execute()
            )
            if not res.data:
                return None
            return MediaFile.model_validate(res.data[0])
        except Exception as e:
            map_supabase_error(e, context=f"get_media_by_id(seller_id={sid}, media_id={mid})")

    def list_media(
        self,
        seller_id: Union[str, UUID],
        purpose: Optional[str] = None,
        media_type: Optional[str] = None,
        customer_id: Optional[Union[str, UUID]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[MediaFile]:
        """
        Lists media records for a seller with optional filters and pagination.
        """
        sid = self._normalize_id(seller_id)
        try:
            query = (
                self.db.table("media_files")
                .select("*")
                .eq("seller_id", sid)
                .order("created_at", desc=True)
                .limit(limit)
                .offset(offset)
            )
            if purpose:
                query = query.eq("purpose", purpose.strip().lower())
            if media_type:
                query = query.eq("media_type", media_type.strip().lower())
            if customer_id:
                cid = self._normalize_id(customer_id)
                query = query.eq("customer_id", cid)

            res = query.execute()
            return [MediaFile.model_validate(row) for row in res.data]
        except Exception as e:
            map_supabase_error(e, context=f"list_media(seller_id={sid})")

    def delete_media_file(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID]
    ) -> bool:
        """
        Deletes a media record owned by seller_id.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        try:
            res = (
                self.db.table("media_files")
                .delete()
                .eq("seller_id", sid)
                .eq("id", mid)
                .execute()
            )
            return len(res.data) > 0
        except Exception as e:
            map_supabase_error(e, context=f"delete_media_file(seller_id={sid}, media_id={mid})")

    def update_processing_status(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID],
        processing_status: str
    ) -> Optional[MediaFile]:
        """
        Updates the processing_status of a media file.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        try:
            res = (
                self.db.table("media_files")
                .update({"processing_status": processing_status.strip().lower()})
                .eq("seller_id", sid)
                .eq("id", mid)
                .execute()
            )
            if not res.data:
                return None
            return MediaFile.model_validate(res.data[0])
        except Exception as e:
            map_supabase_error(e, context=f"update_processing_status(seller_id={sid}, media_id={mid})")

