import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from supabase import Client

from backend.app.core.config import settings
from backend.app.models.media import MediaFile
from backend.app.schemas.media import MediaResponse, MediaUrlResponse
from backend.app.repositories.media_repository import MediaRepository
from backend.app.repositories.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    RepositoryError,
)
from backend.app.utils.file_validation import (
    FileValidationError,
    validate_file_content,
    build_safe_storage_path,
)

logger = logging.getLogger(__name__)


class StorageService:
    """
    Business logic and orchestration service for file storage and media metadata.
    Enforces multi-tenant isolation, MIME signature validation, safe path generation,
    and orphan cleanup.
    """

    def __init__(self, db: Client, bucket: Optional[str] = None):
        self.db = db
        self.bucket = bucket or settings.SUPABASE_STORAGE_BUCKET or "munim-media"
        self.media_repo = MediaRepository(db)

    def _normalize_id(self, val: Union[str, UUID]) -> str:
        return str(val).strip()

    def get_signed_url_string(self, storage_path: str, expires_in: int = 300) -> Optional[str]:
        """
        Helper to generate a short-lived signed URL for a storage path.
        Returns None if generation fails.
        """
        try:
            res = self.db.storage.from_(self.bucket).create_signed_url(
                storage_path, expires_in
            )
            if isinstance(res, dict):
                return res.get("signedURL") or res.get("signedUrl")
            return None
        except Exception as e:
            logger.warning("Failed to generate signed URL for path '%s': %s", storage_path, e)
            return None

    def upload_media(
        self,
        seller_id: Union[str, UUID],
        file_bytes: bytes,
        original_filename: Optional[str] = None,
        declared_content_type: Optional[str] = None,
        category: str = "attachment",
        customer_id: Optional[Union[str, UUID]] = None,
    ) -> MediaResponse:
        """
        Orchestrates secure media upload:
        1. Validates magic bytes, file size, category permissions, and detects path traversal.
        2. Generates safe non-guessable tenant-scoped storage path.
        3. Uploads binary data to Supabase Storage.
        4. Inserts metadata row in media_files.
        5. Handles orphan cleanup if metadata creation fails.
        6. Generates short-lived signed URL for immediate preview.
        """
        sid = self._normalize_id(seller_id)
        cid = self._normalize_id(customer_id) if customer_id else None

        # 1. Validation (raises FileValidationError on invalid size, spoofing, traversal, or unsupported format)
        info = validate_file_content(
            data=file_bytes,
            category=category,
            declared_content_type=declared_content_type,
            original_filename=original_filename,
        )

        # 2. Safe path generation: {seller_id}/{category}/{uuid}{ext}
        media_id = uuid.uuid4()
        storage_path = build_safe_storage_path(
            seller_id=sid,
            category=info.category,
            media_uuid=str(media_id),
            canonical_ext=info.canonical_ext,
        )

        # 3. Upload to Supabase Storage
        upload_successful = False
        try:
            self.db.storage.from_(self.bucket).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": info.verified_mime, "upsert": "false"},
            )
            upload_successful = True
        except Exception as e:
            err_msg = str(e)
            logger.error("Supabase Storage upload failed for '%s': %s", storage_path, err_msg)
            if "row-level security" in err_msg.lower() or "unauthorized" in err_msg.lower():
                raise PermissionDeniedError(f"Permission denied uploading to storage bucket '{self.bucket}'.")
            raise RepositoryError(f"Failed to upload file to storage: {err_msg}")

        # 4. Insert metadata record in PostgreSQL media_files
        try:
            media_file = self.media_repo.create_media_file(
                seller_id=sid,
                storage_bucket=self.bucket,
                storage_path=storage_path,
                media_type=info.media_type,
                purpose=info.category,
                customer_id=cid,
                processing_status="uploaded",
                media_id=media_id,
            )
        except Exception as e:
            # 5. Orphan Cleanup: Delete uploaded storage object if metadata insertion failed
            if upload_successful:
                logger.warning(
                    "Database insertion failed after storage upload for '%s'. Cleaning up orphaned storage object...",
                    storage_path,
                )
                try:
                    self.db.storage.from_(self.bucket).remove([storage_path])
                    logger.info("Successfully cleaned up orphaned storage object '%s'.", storage_path)
                except Exception as cleanup_err:
                    logger.error(
                        "CRITICAL: Failed to clean up orphaned storage object '%s': %s",
                        storage_path,
                        cleanup_err,
                    )
            raise

        # 6. Generate signed URL for immediate consumption
        signed_url = self.get_signed_url_string(storage_path, expires_in=300)

        return MediaResponse(
            id=media_file.id,
            seller_id=media_file.seller_id,
            customer_id=media_file.customer_id,
            storage_bucket=media_file.storage_bucket,
            storage_path=media_file.storage_path,
            media_type=media_file.media_type,
            purpose=media_file.purpose,
            processing_status=media_file.processing_status,
            created_at=media_file.created_at,
            signed_url=signed_url,
        )

    def get_media(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID],
        include_signed_url: bool = True,
    ) -> MediaResponse:
        """
        Retrieves media metadata with strict seller ownership verification.
        Optionally attaches a fresh short-lived signed URL.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        media_file = self.media_repo.get_media_by_id(seller_id=sid, media_id=mid)
        if not media_file:
            raise NotFoundError(f"Media '{mid}' not found or not owned by seller.")

        signed_url = None
        if include_signed_url:
            signed_url = self.get_signed_url_string(media_file.storage_path, expires_in=300)

        return MediaResponse(
            id=media_file.id,
            seller_id=media_file.seller_id,
            customer_id=media_file.customer_id,
            storage_bucket=media_file.storage_bucket,
            storage_path=media_file.storage_path,
            media_type=media_file.media_type,
            purpose=media_file.purpose,
            processing_status=media_file.processing_status,
            created_at=media_file.created_at,
            signed_url=signed_url,
        )

    def get_signed_url(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID],
        expires_in: int = 300,
    ) -> MediaUrlResponse:
        """
        Generates a short-lived signed download URL for an authenticated seller's media.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        if expires_in < 30 or expires_in > 86400:
            raise ValueError("expires_in must be between 30 and 86400 seconds (24 hours).")

        media_file = self.media_repo.get_media_by_id(seller_id=sid, media_id=mid)
        if not media_file:
            raise NotFoundError(f"Media '{mid}' not found or not owned by seller.")

        res = self.db.storage.from_(media_file.storage_bucket).create_signed_url(
            media_file.storage_path, expires_in
        )
        signed_url = None
        if isinstance(res, dict):
            signed_url = res.get("signedURL") or res.get("signedUrl")

        if not signed_url:
            raise RepositoryError(f"Failed to generate signed URL for media '{mid}'.")

        return MediaUrlResponse(signed_url=signed_url, expires_in=expires_in)

    def download_media_bytes(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID],
    ) -> bytes:
        """
        Downloads raw file bytes from Supabase Storage for an authenticated seller's media.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        media_file = self.media_repo.get_media_by_id(seller_id=sid, media_id=mid)
        if not media_file:
            raise NotFoundError(f"Media '{mid}' not found or not owned by seller.")

        try:
            return self.db.storage.from_(media_file.storage_bucket).download(media_file.storage_path)
        except Exception as e:
            logger.error("Failed to download media '%s' from storage: %s", mid, e)
            raise RepositoryError(f"Failed to download media content: {e}")

    def delete_media(
        self,
        seller_id: Union[str, UUID],
        media_id: Union[str, UUID],
    ) -> bool:
        """
        Safely removes a file from both Supabase Storage and media_files table.
        """
        sid = self._normalize_id(seller_id)
        mid = self._normalize_id(media_id)

        media_file = self.media_repo.get_media_by_id(seller_id=sid, media_id=mid)
        if not media_file:
            raise NotFoundError(f"Media '{mid}' not found or not owned by seller.")

        # 1. Delete from Supabase Storage
        try:
            self.db.storage.from_(media_file.storage_bucket).remove([media_file.storage_path])
        except Exception as e:
            logger.warning("Storage remove failed for '%s' (may have already been deleted): %s", media_file.storage_path, e)

        # 2. Delete database metadata
        return self.media_repo.delete_media_file(seller_id=sid, media_id=mid)

