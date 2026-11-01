import os
import re
from dataclasses import dataclass
from typing import Optional, Set
from uuid import UUID

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_CATEGORIES: Set[str] = {
    "upi_proof",
    "voice_note",
    "order_note",
    "product_image",
    "attachment",
}

# MIME types allowed per category
CATEGORY_ALLOWED_MIMES = {
    "upi_proof": {"image/jpeg", "image/png", "image/webp", "application/pdf"},
    "voice_note": {
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/x-m4a",
        "audio/ogg",
        "audio/webm",
        "audio/wav",
        "audio/x-wav",
    },
    "order_note": {"image/jpeg", "image/png", "image/webp", "application/pdf"},
    "product_image": {"image/jpeg", "image/png", "image/webp"},
    "attachment": {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/x-m4a",
        "audio/ogg",
        "audio/webm",
        "audio/wav",
        "audio/x-wav",
    },
}

MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
}

MIME_TO_MEDIA_TYPE = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "application/pdf": "document",
    "audio/mpeg": "audio",
    "audio/mp3": "audio",
    "audio/mp4": "audio",
    "audio/x-m4a": "audio",
    "audio/ogg": "audio",
    "audio/webm": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
}


@dataclass
class ValidatedFileInfo:
    verified_mime: str
    media_type: str
    canonical_ext: str
    size_bytes: int
    category: str


class FileValidationError(ValueError):
    """Raised when file validation fails due to size, type, or spoofing."""
    pass


def detect_mime_type_from_bytes(data: bytes) -> Optional[str]:
    """
    Inspects magic byte headers to determine the genuine MIME type.
    Does not rely on user-supplied headers or extensions.
    """
    if len(data) < 4:
        return None

    # JPEG: FF D8 FF
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG: \x89PNG\r\n\x1a\n
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # PDF: %PDF-
    if data.startswith(b"%PDF-"):
        return "application/pdf"

    # WEBP: RIFF....WEBP
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"

    # WAV: RIFF....WAVE
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "audio/wav"

    # MP3: ID3 tag or MPEG sync word
    if data.startswith(b"ID3"):
        return "audio/mpeg"
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "audio/mpeg"

    # MP4 / M4A: offset 4..8 == 'ftyp'
    if len(data) >= 8 and data[4:8] == b"ftyp":
        return "audio/mp4"

    # OGG: OggS
    if data.startswith(b"OggS"):
        return "audio/ogg"

    # WEBM: EBML header \x1a\x45\xdf\xa3
    if data.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio/webm"

    return None


def validate_file_content(
    data: bytes,
    category: str = "attachment",
    declared_content_type: Optional[str] = None,
    original_filename: Optional[str] = None,
) -> ValidatedFileInfo:
    """
    Validates file payload against size limits, category permissions,
    and anti-spoofing signature verification.
    """
    # 1. Size bounds
    size_bytes = len(data)
    if size_bytes == 0:
        raise FileValidationError("File payload is empty (0 bytes).")
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({size_bytes} bytes) exceeds maximum limit of {MAX_FILE_SIZE_BYTES} bytes (10 MB)."
        )

    # 2. Category validation
    cat = category.strip().lower()
    if cat not in ALLOWED_CATEGORIES:
        raise FileValidationError(
            f"Invalid category '{category}'. Allowed categories: {sorted(ALLOWED_CATEGORIES)}"
        )

    # 3. Path traversal detection in original filename
    if original_filename:
        if ".." in original_filename or "/" in original_filename or "\\" in original_filename or "\0" in original_filename:
            raise FileValidationError("Path traversal characters detected in filename.")

    # 4. Signature / magic bytes validation
    detected_mime = detect_mime_type_from_bytes(data)
    if not detected_mime:
        raise FileValidationError("Unsupported file format or unidentifiable file signature.")

    # 5. Anti-spoofing header check
    if declared_content_type:
        clean_declared = declared_content_type.split(";")[0].strip().lower()
        # Normalize audio types
        if clean_declared == "audio/mp3":
            clean_declared = "audio/mpeg"
        elif clean_declared == "audio/x-m4a":
            clean_declared = "audio/mp4"
        elif clean_declared == "audio/x-wav":
            clean_declared = "audio/wav"

        # Disallow mismatch between detected and declared
        if clean_declared != detected_mime:
            # Allow generic application/octet-stream if signature is recognized
            if clean_declared != "application/octet-stream":
                raise FileValidationError(
                    f"MIME type mismatch: declared '{declared_content_type}' does not match detected format '{detected_mime}'."
                )

    # 6. Category constraint check
    allowed_for_cat = CATEGORY_ALLOWED_MIMES.get(cat, set())
    if detected_mime not in allowed_for_cat:
        raise FileValidationError(
            f"MIME type '{detected_mime}' is not permitted for category '{cat}'."
        )

    media_type = MIME_TO_MEDIA_TYPE[detected_mime]
    canonical_ext = MIME_TO_EXTENSION[detected_mime]

    return ValidatedFileInfo(
        verified_mime=detected_mime,
        media_type=media_type,
        canonical_ext=canonical_ext,
        size_bytes=size_bytes,
        category=cat,
    )


def build_safe_storage_path(
    seller_id: str,
    category: str,
    media_uuid: str,
    canonical_ext: str,
) -> str:
    """
    Builds a secure, tenant-scoped, non-guessable storage path.
    Format: {seller_id}/{category}/{media_uuid}{canonical_ext}
    Never incorporates customer-supplied filenames or untrusted path components.
    """
    clean_seller = str(UUID(seller_id.strip()))
    clean_cat = category.strip().lower()
    clean_uuid = str(UUID(media_uuid.strip()))
    clean_ext = canonical_ext.strip().lower()
    if not clean_ext.startswith("."):
        clean_ext = f".{clean_ext}"

    if clean_cat not in ALLOWED_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'")

    return f"{clean_seller}/{clean_cat}/{clean_uuid}{clean_ext}"

