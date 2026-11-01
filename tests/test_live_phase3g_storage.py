"""
==============================================================================
Munim AI — Live Supabase Storage Integration Test Suite (Phase 3G)
==============================================================================
Tests Phase 3G storage integration directly against remote Supabase:
- Live storage bucket existence ('munim-media')
- Authenticated file upload via POST /api/media/upload
- Real PostgREST metadata record insertion in public.media_files
- Signed URL generation via GET /api/media/{id}/url
- Cross-seller RLS boundary enforcement on live storage and database
- Safe deletion from both storage and PostgreSQL
"""

import io
import os
import uuid
from typing import Optional, Tuple
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from supabase import create_client, Client

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 50


def get_live_seller_tokens() -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Retrieves live JWT tokens for Seller A and Seller B."""
    env = {**dotenv_values(".env"), **os.environ}
    email_a = env.get("TEST_SELLER_A_EMAIL") or env.get("SELLER_A_EMAIL")
    pass_a = env.get("TEST_SELLER_A_PASSWORD") or env.get("SELLER_A_PASSWORD")
    email_b = env.get("TEST_SELLER_B_EMAIL") or env.get("SELLER_B_EMAIL")
    pass_b = env.get("TEST_SELLER_B_PASSWORD") or env.get("SELLER_B_PASSWORD")

    if not email_a or not pass_a or not email_b or not pass_b:
        return None, None, None, None, "Missing test seller credentials in .env"

    try:
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        auth_a = sb.auth.sign_in_with_password({"email": email_a, "password": pass_a})
        token_a = auth_a.session.access_token
        seller_a_id = str(auth_a.user.id)

        auth_b = sb.auth.sign_in_with_password({"email": email_b, "password": pass_b})
        token_b = auth_b.session.access_token
        seller_b_id = str(auth_b.user.id)

        return token_a, seller_a_id, token_b, seller_b_id, None
    except Exception as e:
        return None, None, None, None, f"Supabase auth failed: {e}"


def check_is_live_storage_ready(token: str, seller_id: str) -> Tuple[bool, str]:
    """
    Checks whether migration 20261101_004_storage_bucket_and_policies.sql has been deployed
    and the 'munim-media' bucket is configured and accessible.
    """
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
    sb.options.headers["Authorization"] = f"Bearer {token}"
    sb._storage = None

    bucket_name = settings.SUPABASE_STORAGE_BUCKET or "munim-media"
    probe_path = f"{seller_id}/probe/probe_{uuid.uuid4().hex[:6]}.jpg"

    try:
        sb.storage.from_(bucket_name).upload(
            path=probe_path,
            file=VALID_JPEG,
            file_options={"content-type": "image/jpeg"}
        )
        # Upload succeeded, clean it up
        sb.storage.from_(bucket_name).remove([probe_path])
        return True, "Storage ready"
    except Exception as e:
        err = str(e)
        return False, f"Storage bucket '{bucket_name}' not ready or RLS policy not applied: {err}"


@pytest.mark.live_postgres
class TestLiveSupabaseStorage:
    """Live HTTP endpoint integration tests for Phase 3G against real Supabase Storage."""

    @pytest.fixture(autouse=True)
    def setup_live_tokens(self):
        token_a, seller_a_id, token_b, seller_b_id, error = get_live_seller_tokens()
        if error:
            pytest.skip(f"Live Supabase Auth credentials not available: {error}")
        self.token_a = token_a
        self.seller_a_id = seller_a_id
        self.token_b = token_b
        self.seller_b_id = seller_b_id
        self.headers_a = {"Authorization": f"Bearer {token_a}"}
        self.headers_b = {"Authorization": f"Bearer {token_b}"}

        ready, reason = check_is_live_storage_ready(token_a, seller_a_id)
        if not ready:
            pytest.skip(
                f"Migration '20261101_004_storage_bucket_and_policies.sql' is not yet deployed on live Supabase: {reason}"
            )

    def test_live_storage_full_lifecycle_and_tenant_isolation(self):
        """
        Tests end-to-end media storage lifecycle on real Supabase:
        1. Upload JPEG via POST /api/media/upload
        2. Verify storage path and metadata in PostgreSQL
        3. Retrieve metadata via GET /api/media/{id}
        4. Request fresh signed URL via GET /api/media/{id}/url
        5. Verify Seller B cannot access or delete Seller A's media
        6. Delete media via DELETE /api/media/{id}
        """
        media_id = None
        storage_path = None

        try:
            # 1. Upload
            files = {"file": ("live_receipt.jpg", io.BytesIO(VALID_JPEG), "image/jpeg")}
            data = {"category": "upi_proof"}
            res = client.post("/api/media/upload", files=files, data=data, headers=self.headers_a)
            assert res.status_code == 201, f"Upload failed: {res.text}"
            body = res.json()
            media_id = body["id"]
            storage_path = body["storage_path"]
            assert body["seller_id"] == self.seller_a_id
            assert body["media_type"] == "image"
            assert body["purpose"] == "upi_proof"
            assert storage_path.startswith(f"{self.seller_a_id}/upi_proof/")
            assert body["signed_url"] is not None

            # 2. Get Metadata
            get_res = client.get(f"/api/media/{media_id}", headers=self.headers_a)
            assert get_res.status_code == 200
            assert get_res.json()["id"] == media_id

            # 3. Generate Signed URL
            url_res = client.get(f"/api/media/{media_id}/url?expires_in=600", headers=self.headers_a)
            assert url_res.status_code == 200
            assert "token=" in url_res.json()["signed_url"]

            # 4. Multi-Tenant Isolation: Seller B cannot view Seller A's media
            b_get_res = client.get(f"/api/media/{media_id}", headers=self.headers_b)
            assert b_get_res.status_code == 404

            # Seller B cannot generate signed URL for Seller A's media
            b_url_res = client.get(f"/api/media/{media_id}/url", headers=self.headers_b)
            assert b_url_res.status_code == 404

            # Seller B cannot delete Seller A's media
            b_del_res = client.delete(f"/api/media/{media_id}", headers=self.headers_b)
            assert b_del_res.status_code == 404

            # 5. Delete by Seller A
            del_res = client.delete(f"/api/media/{media_id}", headers=self.headers_a)
            assert del_res.status_code == 204
            media_id = None  # Deleted successfully

        finally:
            # Cleanup if test failed midway
            if media_id:
                try:
                    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
                    sb.options.headers["Authorization"] = f"Bearer {self.token_a}"
                    sb.postgrest.auth(self.token_a)
                    sb._storage = None
                    if storage_path:
                        sb.storage.from_("munim-media").remove([storage_path])
                    sb.table("media_files").delete().eq("id", media_id).execute()
                except Exception:
                    pass

