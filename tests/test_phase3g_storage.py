"""
==============================================================================
Munim AI — Phase 3G: Supabase Storage Integration Unit & Mock Test Suite
==============================================================================
Tests:
- Authenticated uploads with valid magic bytes (JPEG, PNG, WEBP, PDF, MP3)
- Unauthenticated upload rejection (401)
- Invalid MIME types rejection (400)
- Spoofed file extensions and MIME headers (400)
- Category constraint enforcement (e.g. audio rejected for product_image)
- Oversized file rejection (> 10MB)
- Path traversal detection in original filename
- Multi-tenant isolation: Seller B cannot view, sign URL for, or delete Seller A's media (404)
- Signed URL expiration parameter range validation
- Orphan cleanup: Storage upload succeeds but metadata insert fails
- Safe media deletion from both storage and database
- Reusable WhatsApp media download and ingestion helpers
"""

import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.auth import AuthenticatedSeller, get_current_seller
from backend.app.models.media import MediaFile
from backend.app.schemas.media import MediaResponse, MediaUrlResponse
from backend.app.repositories.media_repository import MediaRepository
from backend.app.repositories.exceptions import NotFoundError, PermissionDeniedError
from backend.app.services.storage_service import StorageService
from backend.app.services.whatsapp_media_service import (
    download_whatsapp_provider_media,
    ingest_whatsapp_media,
)
from backend.app.utils.file_validation import (
    FileValidationError,
    validate_file_content,
    build_safe_storage_path,
    detect_mime_type_from_bytes,
)

client = TestClient(app)

SELLER_A_ID = "11111111-1111-1111-1111-111111111111"
SELLER_B_ID = "22222222-2222-2222-2222-222222222222"

# Valid Sample Payloads with True Magic Bytes
VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 50
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
VALID_WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x00\x30\x01\x00\x9d\x01\x2a\x01\x00\x01\x00"
VALID_PDF = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
VALID_MP3 = b"ID3\x03\x00\x00\x00\x00\x00\x20TIT2\x00\x00\x00\x0b\x00\x00\x00Test Audio" + b"\xff\xfb\x90\x44" * 10
VALID_WAV = b"RIFF\x2c\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"


# ============================================================================
# Mock In-Memory Storage & Database
# ============================================================================

class MockBucketProxy:
    def __init__(self, bucket_id: str, storage_store: dict):
        self.bucket_id = bucket_id
        self.storage_store = storage_store

    def upload(self, path: str, file: bytes, file_options: Optional[dict] = None):
        self.storage_store[path] = {
            "content": file if isinstance(file, bytes) else file.read(),
            "options": file_options or {},
        }
        return {"Key": path}

    def remove(self, paths: list):
        for p in paths:
            self.storage_store.pop(p, None)
        return [{"name": p} for p in paths]

    def create_signed_url(self, path: str, expires_in: int, options: Optional[dict] = None):
        if path not in self.storage_store and not path.startswith(f"{SELLER_A_ID}/") and not path.startswith(f"{SELLER_B_ID}/"):
            pass
        url = f"https://mock-storage.supabase.co/object/sign/{self.bucket_id}/{path}?token=mock_token&expires={expires_in}"
        return {"signedURL": url, "signedUrl": url}

    def download(self, path: str):
        if path not in self.storage_store:
            raise RuntimeError(f"Object '{path}' not found in storage.")
        return self.storage_store[path]["content"]


class MockStorageClient:
    def __init__(self, storage_store: dict):
        self.storage_store = storage_store

    def from_(self, bucket_id: str):
        return MockBucketProxy(bucket_id, self.storage_store)


class MockQuery:
    def __init__(self, table_name: str, db_store: dict):
        self.table_name = table_name
        self.db_store = db_store
        self.rows = list(self.db_store.get(table_name, []))
        self._action = "select"
        self._payload = None

    def select(self, *args, **kwargs):
        return self

    def eq(self, column: str, value: Any):
        self.rows = [r for r in self.rows if str(r.get(column)) == str(value)]
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def limit(self, count: int):
        self.rows = self.rows[:count]
        return self

    def offset(self, count: int):
        self.rows = self.rows[count:]
        return self

    def insert(self, payload: Any):
        self._action = "insert"
        self._payload = payload if isinstance(payload, list) else [payload]
        return self

    def delete(self):
        self._action = "delete"
        return self

    def update(self, payload: dict):
        self._action = "update"
        self._payload = payload
        return self

    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data

        if self._action == "insert":
            inserted = []
            for item in self._payload:
                new_row = dict(item)
                if "id" not in new_row or not new_row["id"]:
                    new_row["id"] = str(uuid.uuid4())
                if "created_at" not in new_row or not new_row["created_at"]:
                    new_row["created_at"] = datetime.now(timezone.utc).isoformat()
                self.db_store.setdefault(self.table_name, []).append(new_row)
                inserted.append(new_row)
            return Result(inserted)

        elif self._action == "delete":
            deleted = []
            remaining = []
            del_ids = {r.get("id") for r in self.rows}
            for row in self.db_store.get(self.table_name, []):
                if row.get("id") in del_ids:
                    deleted.append(row)
                else:
                    remaining.append(row)
            self.db_store[self.table_name] = remaining
            return Result(deleted)

        elif self._action == "update":
            updated = []
            upd_ids = {r.get("id") for r in self.rows}
            for row in self.db_store.get(self.table_name, []):
                if row.get("id") in upd_ids:
                    row.update(self._payload)
                    updated.append(dict(row))
            return Result(updated)

        return Result(self.rows)


class MockSupabaseClient:
    def __init__(self, db_store: dict, storage_store: dict):
        self.db_store = db_store
        self.storage_store = storage_store
        self.storage = MockStorageClient(storage_store)

    def table(self, table_name: str):
        return MockQuery(table_name, self.db_store)


@pytest.fixture(autouse=True)
def setup_mock_environment(monkeypatch):
    """Sets up unified in-memory storage and database stores for tests."""
    db_store = {"media_files": []}
    storage_store = {}

    def get_mock_seller(credentials=None):
        return AuthenticatedSeller(
            id=SELLER_A_ID,
            db=MockSupabaseClient(db_store, storage_store),
            access_token="mock_token_a",
        )

    app.dependency_overrides[get_current_seller] = get_mock_seller
    yield {
        "db": db_store,
        "storage": storage_store,
        "get_mock_seller": get_mock_seller,
    }
    app.dependency_overrides.clear()


# ============================================================================
# 1. File Validation & Magic Bytes Tests
# ============================================================================

class TestFileValidationAndSignatures:
    """Verifies file signature checks, MIME type detection, and traversal guards."""

    def test_magic_bytes_detection(self):
        assert detect_mime_type_from_bytes(VALID_JPEG) == "image/jpeg"
        assert detect_mime_type_from_bytes(VALID_PNG) == "image/png"
        assert detect_mime_type_from_bytes(VALID_WEBP) == "image/webp"
        assert detect_mime_type_from_bytes(VALID_PDF) == "application/pdf"
        assert detect_mime_type_from_bytes(VALID_MP3) == "audio/mpeg"
        assert detect_mime_type_from_bytes(VALID_WAV) == "audio/wav"

    def test_spoofed_file_extension_rejected(self):
        # A file declared as JPEG, but content is plain text
        spoofed_payload = b"This is not a real image header!"
        with pytest.raises(FileValidationError, match="Unsupported file format"):
            validate_file_content(spoofed_payload, category="upi_proof", declared_content_type="image/jpeg")

    def test_mismatched_mime_header_rejected(self):
        # Content is PNG, but declared as audio/mpeg
        with pytest.raises(FileValidationError, match="MIME type mismatch"):
            validate_file_content(VALID_PNG, category="attachment", declared_content_type="audio/mpeg")

    def test_category_permission_enforcement(self):
        # Audio is not allowed for product_image
        with pytest.raises(FileValidationError, match="not permitted for category 'product_image'"):
            validate_file_content(VALID_MP3, category="product_image")

    def test_oversized_file_rejected(self):
        oversized = b"\xff\xd8\xff\xe0" + b"\x00" * (10 * 1024 * 1024 + 1)
        with pytest.raises(FileValidationError, match="exceeds maximum limit"):
            validate_file_content(oversized, category="attachment")

    def test_empty_file_rejected(self):
        with pytest.raises(FileValidationError, match="payload is empty"):
            validate_file_content(b"", category="attachment")

    def test_path_traversal_filename_rejected(self):
        with pytest.raises(FileValidationError, match="Path traversal characters detected"):
            validate_file_content(VALID_JPEG, category="attachment", original_filename="../../etc/passwd")

    def test_safe_storage_path_generation(self):
        safe_path = build_safe_storage_path(
            seller_id=SELLER_A_ID,
            category="upi_proof",
            media_uuid="33333333-3333-3333-3333-333333333333",
            canonical_ext=".jpg"
        )
        assert safe_path == f"{SELLER_A_ID}/upi_proof/33333333-3333-3333-3333-333333333333.jpg"


# ============================================================================
# 2. Upload Endpoint & Service Tests
# ============================================================================

class TestMediaUploadEndpoints:
    """Tests POST /api/media/upload and storage service orchestration."""

    def test_authenticated_upload_jpeg_success(self):
        files = {"file": ("receipt.jpg", io.BytesIO(VALID_JPEG), "image/jpeg")}
        data = {"category": "upi_proof"}
        res = client.post("/api/media/upload", files=files, data=data)
        assert res.status_code == 201, f"Upload failed: {res.text}"
        body = res.json()
        assert body["seller_id"] == SELLER_A_ID
        assert body["media_type"] == "image"
        assert body["purpose"] == "upi_proof"
        assert body["storage_path"].startswith(f"{SELLER_A_ID}/upi_proof/")
        assert body["storage_path"].endswith(".jpg")
        assert body["signed_url"] is not None
        assert "mock_token" in body["signed_url"]

    def test_authenticated_upload_voice_note_mp3_success(self):
        files = {"file": ("note.mp3", io.BytesIO(VALID_MP3), "audio/mpeg")}
        data = {"category": "voice_note"}
        res = client.post("/api/media/upload", files=files, data=data)
        assert res.status_code == 201
        body = res.json()
        assert body["media_type"] == "audio"
        assert body["purpose"] == "voice_note"
        assert body["storage_path"].endswith(".mp3")

    def test_unauthenticated_upload_rejected(self):
        app.dependency_overrides.clear()
        files = {"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")}
        res = client.post("/api/media/upload", files=files)
        assert res.status_code == 401

    def test_spoofed_upload_rejected(self):
        files = {"file": ("fake.png", io.BytesIO(b"NOT_A_REAL_PNG"), "image/png")}
        data = {"category": "product_image"}
        res = client.post("/api/media/upload", files=files, data=data)
        assert res.status_code == 400
        assert "Unsupported file format" in res.json()["detail"]

    def test_invalid_category_rejected(self):
        files = {"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")}
        data = {"category": "malicious_category"}
        res = client.post("/api/media/upload", files=files, data=data)
        assert res.status_code == 400
        assert "Invalid category" in res.json()["detail"]


# ============================================================================
# 3. Retrieval, Signed URLs, and Multi-Tenant Isolation
# ============================================================================

class TestMediaRetrievalAndIsolation:
    """Tests GET /api/media/{id}, signed URL generation, and tenant separation."""

    def test_get_media_metadata_success(self):
        # Upload first
        files = {"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")}
        up_res = client.post("/api/media/upload", files=files, data={"category": "product_image"})
        assert up_res.status_code == 201
        media_id = up_res.json()["id"]

        # Retrieve
        get_res = client.get(f"/api/media/{media_id}")
        assert get_res.status_code == 200
        body = get_res.json()
        assert body["id"] == media_id
        assert body["media_type"] == "image"
        assert body["signed_url"] is not None

    def test_get_signed_url_custom_expiry(self):
        files = {"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")}
        up_res = client.post("/api/media/upload", files=files, data={"category": "product_image"})
        media_id = up_res.json()["id"]

        url_res = client.get(f"/api/media/{media_id}/url?expires_in=600")
        assert url_res.status_code == 200
        body = url_res.json()
        assert body["expires_in"] == 600
        assert "expires=600" in body["signed_url"]

    def test_get_signed_url_invalid_expiry_rejected(self):
        files = {"file": ("test.png", io.BytesIO(VALID_PNG), "image/png")}
        up_res = client.post("/api/media/upload", files=files)
        media_id = up_res.json()["id"]

        # Too short (< 30s)
        res_short = client.get(f"/api/media/{media_id}/url?expires_in=10")
        assert res_short.status_code == 422

        # Too long (> 86400s)
        res_long = client.get(f"/api/media/{media_id}/url?expires_in=100000")
        assert res_long.status_code == 422

    def test_cross_seller_isolation(self, setup_mock_environment):
        # Upload file as Seller A
        files = {"file": ("a.jpg", io.BytesIO(VALID_JPEG), "image/jpeg")}
        up_res = client.post("/api/media/upload", files=files, data={"category": "upi_proof"})
        assert up_res.status_code == 201
        media_id = up_res.json()["id"]

        # Switch authentication to Seller B
        env = setup_mock_environment
        app.dependency_overrides[get_current_seller] = lambda: AuthenticatedSeller(
            id=SELLER_B_ID,
            db=MockSupabaseClient(env["db"], env["storage"]),
            access_token="mock_token_b"
        )

        # Seller B attempts to get Seller A's media -> 404
        b_get = client.get(f"/api/media/{media_id}")
        assert b_get.status_code == 404

        # Seller B attempts to generate signed URL -> 404
        b_url = client.get(f"/api/media/{media_id}/url")
        assert b_url.status_code == 404

        # Seller B attempts to delete Seller A's media -> 404
        b_del = client.delete(f"/api/media/{media_id}")
        assert b_del.status_code == 404


# ============================================================================
# 4. Deletion and Orphan Cleanup Tests
# ============================================================================

class TestMediaDeletionAndOrphanCleanup:
    """Verifies safe deletion and orphan storage cleanup on failure."""

    def test_safe_media_deletion(self, setup_mock_environment):
        env = setup_mock_environment
        files = {"file": ("delete_me.png", io.BytesIO(VALID_PNG), "image/png")}
        up_res = client.post("/api/media/upload", files=files, data={"category": "product_image"})
        assert up_res.status_code == 201
        media_id = up_res.json()["id"]
        storage_path = up_res.json()["storage_path"]

        # Confirm stored in both mock db and storage
        assert storage_path in env["storage"]
        assert len(env["db"]["media_files"]) == 1

        # Delete
        del_res = client.delete(f"/api/media/{media_id}")
        assert del_res.status_code == 204

        # Confirm removed from both
        assert storage_path not in env["storage"]
        assert len(env["db"]["media_files"]) == 0

        # Second delete returns 404
        del_res2 = client.delete(f"/api/media/{media_id}")
        assert del_res2.status_code == 404

    def test_orphan_cleanup_when_db_insert_fails(self, setup_mock_environment, monkeypatch):
        """
        If file upload succeeds to storage, but database insert raises an error,
        the service must clean up the uploaded storage object.
        """
        env = setup_mock_environment
        mock_db = MockSupabaseClient(env["db"], env["storage"])
        service = StorageService(mock_db)

        # Force database insertion failure
        def fail_create(*args, **kwargs):
            raise RuntimeError("Simulated database failure during media_files insert")

        monkeypatch.setattr(service.media_repo, "create_media_file", fail_create)

        # Upload should fail with RuntimeError
        with pytest.raises(RuntimeError, match="Simulated database failure"):
            service.upload_media(
                seller_id=SELLER_A_ID,
                file_bytes=VALID_JPEG,
                category="upi_proof"
            )

        # Crucial check: Storage must NOT have any orphan files left behind!
        assert len(env["storage"]) == 0
        assert len(env["db"]["media_files"]) == 0


# ============================================================================
# 5. WhatsApp Media Preparation Tests
# ============================================================================

class TestWhatsAppMediaHelpers:
    """Tests download_whatsapp_provider_media and ingest_whatsapp_media."""

    def test_download_whatsapp_media_success(self, monkeypatch):
        class MockResponse:
            status_code = 200
            headers = {"content-type": "image/jpeg", "content-length": str(len(VALID_JPEG))}
            content = VALID_JPEG

        def mock_get(url, **kwargs):
            return MockResponse()

        import httpx
        monkeypatch.setattr(httpx.Client, "get", lambda self, url, **kw: MockResponse())

        data, ctype = download_whatsapp_provider_media("https://api.twilio.com/media/test")
        assert data == VALID_JPEG
        assert ctype == "image/jpeg"

    def test_download_whatsapp_media_rejects_insecure_url(self):
        with pytest.raises(ValueError, match="must be a valid secure HTTPS URL"):
            download_whatsapp_provider_media("http://insecure.com/media.jpg")

    def test_download_whatsapp_media_rejects_oversized_content_length(self, monkeypatch):
        class MockOversizedResponse:
            status_code = 200
            headers = {"content-type": "image/jpeg", "content-length": str(20 * 1024 * 1024)}
            content = b""

        import httpx
        monkeypatch.setattr(httpx.Client, "get", lambda self, url, **kw: MockOversizedResponse())

        with pytest.raises(FileValidationError, match="Provider Content-Length"):
            download_whatsapp_provider_media("https://api.twilio.com/media/huge.jpg")

    def test_ingest_whatsapp_media_end_to_end(self, setup_mock_environment, monkeypatch):
        env = setup_mock_environment
        mock_db = MockSupabaseClient(env["db"], env["storage"])
        service = StorageService(mock_db)

        class MockResponse:
            status_code = 200
            headers = {"content-type": "image/jpeg", "content-length": str(len(VALID_JPEG))}
            content = VALID_JPEG

        import httpx
        monkeypatch.setattr(httpx.Client, "get", lambda self, url, **kw: MockResponse())

        media_resp = ingest_whatsapp_media(
            storage_service=service,
            seller_id=SELLER_A_ID,
            media_url="https://api.twilio.com/2010-04-01/Accounts/AC123/Messages/MM123/Media/ME123",
            category="upi_proof"
        )

        assert media_resp.seller_id == uuid.UUID(SELLER_A_ID)
        assert media_resp.media_type == "image"
        assert media_resp.purpose == "upi_proof"
        assert len(env["storage"]) == 1
        assert len(env["db"]["media_files"]) == 1

