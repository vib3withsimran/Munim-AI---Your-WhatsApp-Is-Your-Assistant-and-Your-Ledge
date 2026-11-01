import logging
from typing import Optional, Tuple, Union
from uuid import UUID
import httpx

from backend.app.schemas.media import MediaResponse
from backend.app.services.storage_service import StorageService
from backend.app.utils.file_validation import (
    FileValidationError,
    MAX_FILE_SIZE_BYTES,
)

logger = logging.getLogger(__name__)


def download_whatsapp_provider_media(
    media_url: str,
    auth: Optional[Tuple[str, str]] = None,
    max_size_bytes: int = MAX_FILE_SIZE_BYTES,
    timeout_seconds: float = 30.0,
) -> Tuple[bytes, str]:
    """
    Downloads media from WhatsApp Cloud API or Twilio API over HTTPS.
    Validates provider response, content type, and enforces size limits.

    Parameters:
    - media_url: Direct download URL provided by Twilio or Meta WhatsApp webhook
    - auth: Basic auth (e.g. (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)) or None for Meta (Bearer token)
    - max_size_bytes: Maximum allowed byte count (default 10 MB)
    - timeout_seconds: HTTP client timeout
    """
    if not media_url or not media_url.startswith("https://"):
        raise ValueError("Media URL must be a valid secure HTTPS URL.")

    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as http_client:
        response = http_client.get(media_url, auth=auth)

        if response.status_code != 200:
            raise RuntimeError(
                f"WhatsApp media download failed with status {response.status_code}: {response.text[:200]}"
            )

        content_length_header = response.headers.get("content-length")
        if content_length_header and int(content_length_header) > max_size_bytes:
            raise FileValidationError(
                f"Provider Content-Length ({content_length_header} bytes) exceeds limit of {max_size_bytes} bytes."
            )

        data = response.content
        if len(data) > max_size_bytes:
            raise FileValidationError(
                f"Downloaded media payload ({len(data)} bytes) exceeds limit of {max_size_bytes} bytes."
            )

        content_type = response.headers.get("content-type", "application/octet-stream")
        return data, content_type


def ingest_whatsapp_media(
    storage_service: StorageService,
    seller_id: Union[str, UUID],
    media_url: str,
    auth: Optional[Tuple[str, str]] = None,
    category: str = "attachment",
    customer_id: Optional[Union[str, UUID]] = None,
) -> MediaResponse:
    """
    Downloads media from provider and securely ingests it into seller-scoped private storage.
    Does not expose customer-provided filenames or untrusted paths.
    """
    data, content_type = download_whatsapp_provider_media(media_url=media_url, auth=auth)

    return storage_service.upload_media(
        seller_id=seller_id,
        file_bytes=data,
        declared_content_type=content_type,
        category=category,
        customer_id=customer_id,
    )

