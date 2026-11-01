import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.schemas.media import MediaResponse, MediaUrlResponse
from backend.app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["Media"])


@router.post(
    "/upload",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload media attachment",
    description="Uploads a file to seller-scoped private Supabase Storage, validates signatures, and returns metadata.",
)
async def upload_media(
    file: UploadFile = File(..., description="File binary payload"),
    category: str = Form(default="attachment", description="Business category ('upi_proof', 'voice_note', 'order_note', 'product_image', 'attachment')"),
    customer_id: Optional[UUID] = Form(default=None, description="Optional customer ID associated with this media"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
):
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file payload: {e}",
        )

    service = StorageService(seller.db)
    return service.upload_media(
        seller_id=seller.id,
        file_bytes=content,
        original_filename=file.filename,
        declared_content_type=file.content_type,
        category=category,
        customer_id=customer_id,
    )


@router.get(
    "/{media_id}",
    response_model=MediaResponse,
    status_code=status.HTTP_200_OK,
    summary="Get media metadata",
    description="Retrieves metadata and a fresh signed URL for an existing media file owned by the authenticated seller.",
)
def get_media(
    media_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
):
    service = StorageService(seller.db)
    return service.get_media(seller_id=seller.id, media_id=media_id)


@router.get(
    "/{media_id}/url",
    response_model=MediaUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate signed URL",
    description="Generates a short-lived signed download URL for an authenticated seller's private media file.",
)
def get_signed_url(
    media_id: UUID,
    expires_in: int = Query(default=300, ge=30, le=86400, description="Validity duration in seconds (30s to 24h)"),
    seller: AuthenticatedSeller = Depends(get_current_seller),
):
    service = StorageService(seller.db)
    return service.get_signed_url(seller_id=seller.id, media_id=media_id, expires_in=expires_in)


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete media file",
    description="Permanently removes a file from Supabase Storage and deletes its database record.",
)
def delete_media(
    media_id: UUID,
    seller: AuthenticatedSeller = Depends(get_current_seller),
):
    service = StorageService(seller.db)
    service.delete_media(seller_id=seller.id, media_id=media_id)
    return None

