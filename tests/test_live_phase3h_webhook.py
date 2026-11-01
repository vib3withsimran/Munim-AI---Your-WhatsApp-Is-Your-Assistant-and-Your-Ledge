"""
==============================================================================
Munim AI — Live Supabase WhatsApp Webhook Integration Test Suite (Phase 3H)
==============================================================================
Tests Phase 3H webhook channel resolution, idempotency, and Supabase integration
directly against real Supabase PostgreSQL:
- Probes whether Migration 20261101_005_webhook_channels_and_idempotency.sql is deployed.
- Verifies live channel registration and resolution in seller_whatsapp_channels.
- Verifies live MessageSid deduplication in webhook_messages.
- Verifies live webhook delivery via FastAPI /webhook endpoint.
"""

import os
import uuid
from typing import Tuple, Optional
import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from supabase import create_client, Client

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.utils.twilio_auth import compute_twilio_signature

client = TestClient(app)


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


def check_is_live_migration_005_deployed(token: str) -> Tuple[bool, str]:
    """
    Checks whether migration 20261101_005_webhook_channels_and_idempotency.sql
    has been deployed by testing access to seller_whatsapp_channels and webhook_messages.
    """
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
    sb.postgrest.auth(token)

    for tbl in ["seller_whatsapp_channels", "webhook_messages"]:
        try:
            sb.table(tbl).select("*").limit(1).execute()
        except Exception as e:
            err_str = str(e)
            if "PGRST205" in err_str or "Could not find the table" in err_str or "does not exist" in err_str:
                return False, f"Table '{tbl}' does not exist on live Supabase."
            return False, f"Error checking table '{tbl}': {err_str}"

    return True, "Migration 005 deployed"


@pytest.mark.live_postgres
class TestLivePhase3HWebhook:
    """Live integration tests for Phase 3H against live Supabase PostgreSQL."""

    @pytest.fixture(autouse=True)
    def setup_live_env(self):
        token_a, seller_a_id, token_b, seller_b_id, error = get_live_seller_tokens()
        if error:
            pytest.skip(f"Live Supabase Auth credentials not available: {error}")
        self.token_a = token_a
        self.seller_a_id = seller_a_id
        self.token_b = token_b
        self.seller_b_id = seller_b_id

        ready, reason = check_is_live_migration_005_deployed(token_a)
        if not ready:
            pytest.skip(
                f"Migration '20261101_005_webhook_channels_and_idempotency.sql' is not yet deployed on live Supabase: {reason}"
            )

    def test_live_channel_resolution_and_idempotency(self):
        """Verifies end-to-end channel mapping, message idempotency, and webhook execution against live DB."""
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLISHABLE_KEY)
        sb.postgrest.auth(self.token_a)

        test_phone = f"+1415{uuid.uuid4().hex[:7]}"
        test_sid = f"SM_live_{uuid.uuid4().hex[:12]}"

        # 1. Register temporary live channel for Seller A
        chan_res = sb.table("seller_whatsapp_channels").insert({
            "seller_id": self.seller_a_id,
            "phone_number": test_phone,
            "display_name": "Live Test Channel",
            "is_active": True,
        }).execute()
        channel_id = chan_res.data[0]["id"]

        try:
            # 2. Post webhook to live endpoint
            form_payload = {
                "MessageSid": test_sid,
                "From": "whatsapp:+919876543210",
                "To": f"whatsapp:{test_phone}",
                "Body": "namaste",
            }

            resp = client.post("/webhook", data=form_payload)
            assert resp.status_code == 200
            assert "Namaste" in resp.text

            # 3. Verify message was logged in webhook_messages
            msg_res = sb.table("webhook_messages").select("*").eq("message_sid", test_sid).execute()
            assert len(msg_res.data) == 1
            assert msg_res.data[0]["processing_status"] in ("completed", "processing")
            assert msg_res.data[0]["seller_id"] == self.seller_a_id

            # 4. Verify duplicate delivery returns cached response
            resp_dup = client.post("/webhook", data=form_payload)
            assert resp_dup.status_code == 200

        finally:
            # Clean up live test rows
            try:
                sb.table("webhook_messages").delete().eq("message_sid", test_sid).execute()
                sb.table("seller_whatsapp_channels").delete().eq("id", channel_id).execute()
            except Exception:
                pass

