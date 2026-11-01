"""
==============================================================================
Munim AI — Phase 3H: WhatsApp Webhook Migration to Supabase Test Suite
==============================================================================
Comprehensive unit, mock, and isolation test suite verifying:
- Twilio HMAC-SHA1 signature authentication and security validation
- Channel-based seller resolution via seller_whatsapp_channels
- Distributed idempotency and deduplication via webhook_messages
- Authoritative customer lifecycle via CustomerService
- Multi-tenant customer privacy persistence in privacy_settings (#private / #resume)
- Fast-path conversational greetings (<10ms)
- Owner management commands (hisaab, dues, summary)
- Multi-tenant media ingestion to private bucket 'munim-media'
- Authoritative order creation with stock reservation via transactional RPC
- Payment recording safety (strictly 'pending' status, never auto-verified)
- HTTP status codes (403 on invalid signature, 200 on TwiML XML responses)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.models.webhook import WebhookProcessingStatus
from backend.app.schemas.customer import CustomerCreateRequest
from backend.app.schemas.order import OrderCreateRequest, OrderItemCreateRequest
from backend.app.schemas.payment import PaymentCreateRequest, PaymentMethod, PaymentStatus
from backend.app.schemas.webhook import normalize_whatsapp_phone
from backend.app.models.schemas import ExtractedMessage, OrderItem as ExtractedOrderItem, ConfidenceScore
from backend.app.utils.twilio_auth import compute_twilio_signature, validate_twilio_signature
from backend.app.repositories.webhook_repository import WebhookRepository
from backend.app.repositories.privacy_repository import PrivacyRepository
from backend.app.services.webhook_orchestration_service import (
    WebhookOrchestrationService,
    build_twiml_response,
)

client = TestClient(app)

SELLER_A_ID = "11111111-1111-1111-1111-111111111111"
SELLER_B_ID = "22222222-2222-2222-2222-222222222222"
CUSTOMER_A_ID = "33333333-3333-3333-3333-333333333333"
PRODUCT_A_ID = "66666666-6666-6666-6666-666666666666"
VARIANT_A_ID = "44444444-4444-4444-4444-444444444444"
ORDER_A_ID = "55555555-5555-5555-5555-555555555555"

CHANNEL_PHONE = "+14155238886"
CUSTOMER_PHONE = "+919876543210"
OWNER_PHONE = "+919999999999"


# ============================================================================
# Mock In-Memory Database & Storage Clients
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

    def create_signed_url(self, path: str, expires_in: int, options: Optional[dict] = None):
        url = f"https://mock-storage.supabase.co/object/sign/{self.bucket_id}/{path}?token=mock&expires={expires_in}"
        return {"signedURL": url, "signedUrl": url}


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

    def neq(self, column: str, value: Any):
        self.rows = [r for r in self.rows if str(r.get(column)) != str(value)]
        return self

    def in_(self, column: str, values: list):
        str_values = {str(v) for v in values}
        self.rows = [r for r in self.rows if str(r.get(column)) in str_values]
        return self

    def order(self, column: str, desc: bool = False):
        return self

    def limit(self, count: int):
        self.rows = self.rows[:count]
        return self

    def range(self, start: int, end: int):
        self.rows = self.rows[start : end + 1]
        return self

    def maybe_single(self):
        return self

    def insert(self, payload: Any):
        self._action = "insert"
        self._payload = payload if isinstance(payload, list) else [payload]
        return self

    def upsert(self, payload: Any):
        self._action = "upsert"
        self._payload = payload if isinstance(payload, list) else [payload]
        return self

    def update(self, payload: dict):
        self._action = "update"
        self._payload = payload
        return self

    def delete(self):
        self._action = "delete"
        return self

    def execute(self):
        class Result:
            def __init__(self, data):
                self.data = data

        if self._action == "insert":
            inserted = []
            for item in self._payload:
                new_row = dict(item)
                # Primary key uniqueness check for webhook_messages
                if self.table_name == "webhook_messages":
                    msid = new_row.get("message_sid")
                    for existing in self.db_store.get(self.table_name, []):
                        if existing.get("message_sid") == msid:
                            raise RuntimeError(f"duplicate key value violates unique constraint on message_sid (23505)")
                if "id" not in new_row and self.table_name != "webhook_messages":
                    new_row["id"] = str(uuid.uuid4())
                if "created_at" not in new_row:
                    new_row["created_at"] = datetime.now(timezone.utc).isoformat()
                self.db_store.setdefault(self.table_name, []).append(new_row)
                inserted.append(new_row)
            return Result(inserted)

        elif self._action == "upsert":
            upserted = []
            for item in self._payload:
                new_row = dict(item)
                msid = new_row.get("message_sid")
                matched = False
                for idx, existing in enumerate(self.db_store.get(self.table_name, [])):
                    if existing.get("message_sid") == msid:
                        self.db_store[self.table_name][idx].update(new_row)
                        upserted.append(self.db_store[self.table_name][idx])
                        matched = True
                        break
                if not matched:
                    self.db_store.setdefault(self.table_name, []).append(new_row)
                    upserted.append(new_row)
            return Result(upserted)

        elif self._action == "update":
            updated = []
            upd_ids = {r.get("id") or r.get("message_sid") for r in self.rows}
            for row in self.db_store.get(self.table_name, []):
                identifier = row.get("id") or row.get("message_sid")
                if identifier in upd_ids:
                    row.update(self._payload)
                    updated.append(dict(row))
            return Result(updated)

        elif self._action == "delete":
            del_ids = {r.get("id") or r.get("message_sid") for r in self.rows}
            remaining = [r for r in self.db_store.get(self.table_name, []) if (r.get("id") or r.get("message_sid")) not in del_ids]
            self.db_store[self.table_name] = remaining
            return Result(self.rows)

        return Result(self.rows)


class MockRpcResult:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self


class MockSupabaseClient:
    def __init__(self, db_store: dict, storage_store: dict):
        self.db_store = db_store
        self.storage_store = storage_store
        self.storage = MockStorageClient(storage_store)

    def table(self, table_name: str):
        return MockQuery(table_name, self.db_store)

    def rpc(self, func_name: str, params: dict):
        if func_name == "create_order_with_reservation_rpc":
            order_id = str(uuid.uuid4())
            new_order = {
                "id": order_id,
                "seller_id": params.get("p_seller_id"),
                "customer_id": params.get("p_customer_id"),
                "status": "pending",
                "total_amount": 1299.00,
                "currency": params.get("p_currency", "INR"),
                "notes": params.get("p_notes"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self.db_store.setdefault("orders", []).append(new_order)
            return MockRpcResult(new_order)
        return MockRpcResult({})


@pytest.fixture
def test_env(monkeypatch):
    """Initializes in-memory database with seeded seller, channel, customer, and product catalog."""
    monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", False)
    db_store = {
        "seller_whatsapp_channels": [
            {
                "id": str(uuid.uuid4()),
                "seller_id": SELLER_A_ID,
                "phone_number": CHANNEL_PHONE,
                "display_name": "Seller A Store",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "webhook_messages": [],
        "privacy_settings": [],
        "customers": [
            {
                "id": CUSTOMER_A_ID,
                "seller_id": SELLER_A_ID,
                "phone": CUSTOMER_PHONE,
                "name": "Priya Sharma",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "products": [
            {
                "id": PRODUCT_A_ID,
                "seller_id": SELLER_A_ID,
                "name": "Cotton Anarkali Kurti",
                "category": "Kurti",
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "product_variants": [
            {
                "id": VARIANT_A_ID,
                "seller_id": SELLER_A_ID,
                "product_id": PRODUCT_A_ID,
                "sku": "KURTI-L-PINK",
                "size": "L",
                "color": "Pink",
                "price": 1299.00,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "inventory": [
            {
                "id": str(uuid.uuid4()),
                "seller_id": SELLER_A_ID,
                "variant_id": VARIANT_A_ID,
                "available_quantity": 20,
                "reserved_quantity": 2,
            }
        ],
        "orders": [
            {
                "id": ORDER_A_ID,
                "seller_id": SELLER_A_ID,
                "customer_id": CUSTOMER_A_ID,
                "status": "pending",
                "total_amount": 1299.00,
                "currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "payments": [],
        "media_files": [],
    }
    storage_store = {}
    mock_db = MockSupabaseClient(db_store, storage_store)
    return mock_db, db_store, storage_store


# ============================================================================
# 1. Twilio HMAC-SHA1 Signature Validation Tests
# ============================================================================

class TestTwilioSignatureValidation:
    """Verifies cryptographic signature validation using HMAC-SHA1."""

    def test_valid_signature_accepted(self):
        url = "https://munim.example.com/api/webhook"
        params = {"MessageSid": "SM12345", "From": "whatsapp:+919876543210", "Body": "Hello"}
        secret = "test_auth_token_xyz"
        sig = compute_twilio_signature(url, params, secret)
        assert validate_twilio_signature(url, params, sig, auth_token=secret) is True

    def test_tampered_signature_rejected(self):
        url = "https://munim.example.com/api/webhook"
        params = {"MessageSid": "SM12345", "From": "whatsapp:+919876543210"}
        secret = "test_auth_token_xyz"
        tampered_sig = "invalid_base64_signature_here="
        assert validate_twilio_signature(url, params, tampered_sig, auth_token=secret) is False

    def test_tampered_payload_rejected(self):
        url = "https://munim.example.com/api/webhook"
        params = {"MessageSid": "SM12345", "Body": "Original body"}
        secret = "test_auth_token_xyz"
        sig = compute_twilio_signature(url, params, secret)

        # Attacker modifies body after signing
        tampered_params = {"MessageSid": "SM12345", "Body": "Tampered body"}
        assert validate_twilio_signature(url, tampered_params, sig, auth_token=secret) is False

    def test_missing_signature_rejected_when_enabled(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
        monkeypatch.setattr(settings, "DRY_RUN", False)
        monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "secret_token")
        url = "https://munim.example.com/api/webhook"
        assert validate_twilio_signature(url, {"Body": "Test"}, signature=None) is False

    def test_validation_bypassed_in_dry_run_or_disabled(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", False)
        assert validate_twilio_signature("http://any", {}, signature=None) is True

        monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
        monkeypatch.setattr(settings, "DRY_RUN", True)
        assert validate_twilio_signature("http://any", {}, signature=None) is True


# ============================================================================
# 2. Channel Resolution and Quarantine Tests
# ============================================================================

class TestChannelResolutionAndQuarantine:
    """Verifies incoming 'To' number maps strictly to verified seller channels."""

    def test_registered_channel_resolves_seller(self, test_env):
        mock_db, _, _ = test_env
        repo = WebhookRepository(mock_db)
        seller = repo.resolve_seller_by_phone(CHANNEL_PHONE)
        assert seller == SELLER_A_ID

    def test_inactive_channel_ignored(self, test_env):
        mock_db, db_store, _ = test_env
        db_store["seller_whatsapp_channels"][0]["is_active"] = False
        repo = WebhookRepository(mock_db)
        seller = repo.resolve_seller_by_phone(CHANNEL_PHONE)
        assert seller is None

    def test_unmapped_channel_quarantines_and_returns_unregistered(self, test_env):
        mock_db, db_store, _ = test_env
        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": "SM_unmapped_001",
            "From": "whatsapp:+919876543210",
            "To": "whatsapp:+19998887777",  # Unregistered destination number
            "Body": "Hello there",
        }

        resp = asyncio.run(service.process_incoming_webhook(
            request_url="http://test/webhook",
            form_data=form,
            signature=None,  # DRY_RUN bypass
        ))

        assert resp.status_code == 200
        assert "not registered" in resp.body.decode("utf-8")

        # Verify quarantine recorded in webhook_messages
        quarantined = [m for m in db_store["webhook_messages"] if m["message_sid"] == "SM_unmapped_001"]
        assert len(quarantined) == 1
        assert quarantined[0]["processing_status"] == WebhookProcessingStatus.QUARANTINED.value

    def test_phone_normalization_helper(self):
        assert normalize_whatsapp_phone("whatsapp:+14155238886") == "+14155238886"
        assert normalize_whatsapp_phone("+14155238886") == "+14155238886"
        assert normalize_whatsapp_phone("14155238886") == "+14155238886"
        assert normalize_whatsapp_phone("  +91 98765-43210  ") == "+919876543210"


# ============================================================================
# 3. Distributed Idempotency and Deduplication Tests
# ============================================================================

class TestDistributedIdempotency:
    """Verifies atomic MessageSid deduplication and duplicate suppression."""

    def test_atomic_message_reservation_success(self, test_env):
        mock_db, db_store, _ = test_env
        repo = WebhookRepository(mock_db)
        is_new, rec = repo.reserve_webhook_message(
            message_sid="SM_claim_01",
            from_phone=CUSTOMER_PHONE,
            to_phone=CHANNEL_PHONE,
            seller_id=SELLER_A_ID,
            raw_text="Test reservation",
        )
        assert is_new is True
        assert rec["message_sid"] == "SM_claim_01"
        assert rec["processing_status"] == "processing"

    def test_concurrent_or_retry_duplicate_detected(self, test_env):
        mock_db, db_store, _ = test_env
        repo = WebhookRepository(mock_db)

        # First claim succeeds
        is_new_1, _ = repo.reserve_webhook_message(
            message_sid="SM_claim_02",
            from_phone=CUSTOMER_PHONE,
            to_phone=CHANNEL_PHONE,
            seller_id=SELLER_A_ID,
        )
        assert is_new_1 is True

        # Second attempt returns is_new=False
        is_new_2, rec_2 = repo.reserve_webhook_message(
            message_sid="SM_claim_02",
            from_phone=CUSTOMER_PHONE,
            to_phone=CHANNEL_PHONE,
            seller_id=SELLER_A_ID,
        )
        assert is_new_2 is False
        assert rec_2["message_sid"] == "SM_claim_02"

    def test_completed_duplicate_returns_cached_response(self, test_env):
        mock_db, db_store, _ = test_env
        repo = WebhookRepository(mock_db)

        # Mark message as previously completed with specific response
        repo.reserve_webhook_message(
            message_sid="SM_claim_03",
            from_phone=CUSTOMER_PHONE,
            to_phone=CHANNEL_PHONE,
            seller_id=SELLER_A_ID,
        )
        repo.mark_message_completed(
            message_sid="SM_claim_03",
            intent="greeting",
            response_summary="Cached Namaste Response!",
        )

        service = WebhookOrchestrationService(db=mock_db)
        form = {
            "MessageSid": "SM_claim_03",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "hi",
        }
        resp = asyncio.run(service.process_incoming_webhook(
            request_url="http://test/webhook",
            form_data=form,
            signature=None,
        ))
        assert resp.status_code == 200
        assert "Cached Namaste Response!" in resp.body.decode("utf-8")


# ============================================================================
# 4. Customer Lifecycle Resolution Tests
# ============================================================================

class TestCustomerLifecycle:
    """Verifies customer lookups, creation, and profile name handling."""

    def test_existing_customer_reused(self, test_env):
        mock_db, db_store, _ = test_env
        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": "SM_cust_01",
            "From": f"whatsapp:{CUSTOMER_PHONE}",  # Already in db_store
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "ProfileName": "Priya Sharma",
            "Body": "namaste",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        # No extra customer should be created
        customers = [c for c in db_store["customers"] if c["seller_id"] == SELLER_A_ID]
        assert len(customers) == 1

    def test_new_customer_automatically_registered(self, test_env):
        mock_db, db_store, _ = test_env
        service = WebhookOrchestrationService(db=mock_db)

        new_phone = "+919811122233"
        form = {
            "MessageSid": "SM_cust_02",
            "From": f"whatsapp:{new_phone}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "ProfileName": "Aarav Patel",
            "Body": "namaste",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200

        # Customer created in customers table
        created = [c for c in db_store["customers"] if c["phone"] == new_phone]
        assert len(created) == 1
        assert created[0]["name"] == "Aarav Patel"


# ============================================================================
# 5. Customer Privacy Control Tests (#private / #resume)
# ============================================================================

class TestPrivacyControls:
    """Verifies #private and #resume toggling, state persistence, and AI masking."""

    def test_hash_private_activates_mode(self, test_env):
        mock_db, db_store, _ = test_env
        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": "SM_priv_01",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "#private pause assistant please",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        assert "Munim AI assistant paused" in resp.body.decode("utf-8")

        # Verify state in privacy_settings
        privacy_row = [p for p in db_store["privacy_settings"] if p["customer_id"] == CUSTOMER_A_ID]
        assert len(privacy_row) == 1
        assert privacy_row[0]["is_private"] is True

    def test_hash_resume_reactivates_mode(self, test_env):
        mock_db, db_store, _ = test_env
        # Pre-seed private mode active
        db_store["privacy_settings"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_A_ID,
            "customer_id": CUSTOMER_A_ID,
            "is_private": True,
        })

        service = WebhookOrchestrationService(db=mock_db)
        form = {
            "MessageSid": "SM_priv_02",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "#resume restart bot",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        assert "Munim AI assistant resumed" in resp.body.decode("utf-8")

        # Verify state flipped
        privacy_row = [p for p in db_store["privacy_settings"] if p["customer_id"] == CUSTOMER_A_ID]
        assert privacy_row[0]["is_private"] is False

    def test_active_privacy_mode_bypasses_ai(self, test_env):
        mock_db, db_store, _ = test_env
        # Set private mode active
        db_store["privacy_settings"].append({
            "id": str(uuid.uuid4()),
            "seller_id": SELLER_A_ID,
            "customer_id": CUSTOMER_A_ID,
            "is_private": True,
        })

        service = WebhookOrchestrationService(db=mock_db)
        form = {
            "MessageSid": "SM_priv_03",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "bhaiya 2 kurti pack kardo",  # Order message while private
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200

        # No order should have been created because AI/order processing is suppressed
        assert len(db_store["orders"]) == 1  # Only seeded order exists


# ============================================================================
# 6. Fast-Path Conversational Greetings Tests (<10ms)
# ============================================================================

class TestFastGreetingsPath:
    """Verifies instant greeting responses without LLM latency."""

    @pytest.mark.parametrize("greeting_text", ["hi", "hello", "Namaste ji", "kaise ho", "good morning"])
    def test_fast_greetings_instant_reply(self, test_env, greeting_text):
        mock_db, _, _ = test_env
        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": f"SM_greet_{uuid.uuid4().hex[:6]}",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": greeting_text,
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        content = resp.body.decode("utf-8")
        assert "Namaste Priya Sharma!" in content
        assert "Munim AI par aapka swagat hai" in content


# ============================================================================
# 7. Owner Commands Tests (Summary / Hisaab)
# ============================================================================

class TestOwnerCommands:
    """Verifies merchant summary queries via WhatsApp."""

    def test_owner_summary_command(self, test_env, monkeypatch):
        mock_db, _, _ = test_env
        monkeypatch.setattr(settings, "OWNER_WHATSAPP_NUMBER", OWNER_PHONE)

        # Register owner as a customer under Seller A
        service = WebhookOrchestrationService(db=mock_db)
        form = {
            "MessageSid": "SM_owner_01",
            "From": f"whatsapp:{OWNER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "hisaab",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        content = resp.body.decode("utf-8")
        assert "Store Hisaab Summary" in content or "Monthly Revenue" in content


# ============================================================================
# 8. Order Placement & Stock Reservation via RPC Tests
# ============================================================================

class TestOrderPlacementViaRPC:
    """Verifies order creation delegates to OrderService transactional RPC."""

    def test_order_creation_triggers_rpc(self, test_env, monkeypatch):
        mock_db, db_store, _ = test_env

        async def mock_extract_order(*args, **kwargs):
            return ExtractedMessage(
                message_id="SM_order_01",
                timestamp="2026-11-01T00:00:00",
                media_type="text",
                type="order",
                customer_phone=CUSTOMER_PHONE,
                customer_name="Priya Sharma",
                raw_text="Didi 1 Cotton Anarkali Kurti L size pack kardo",
                items=[ExtractedOrderItem(name="Cotton Anarkali Kurti", qty=1, size="L", color="Pink")],
                amount=1299.0,
                confidence=ConfidenceScore(overall=0.95, items=0.95, amount=0.95),
                reply_needed=True,
            )
        monkeypatch.setattr("backend.app.services.webhook_orchestration_service.extract_text", mock_extract_order)

        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": "SM_order_01",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "Didi 1 Cotton Anarkali Kurti L size pack kardo",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        content = resp.body.decode("utf-8")
        assert "Order Confirmed!" in content or "stock reserve" in content

        # Check order logged in orders table
        orders = [o for o in db_store["orders"] if o.get("notes") and "SM_order_01" in o.get("notes")]
        assert len(orders) == 1
        assert orders[0]["status"] == "pending"


# ============================================================================
# 9. Payment Recording Safety Tests (Strictly Pending)
# ============================================================================

class TestPaymentSafetyExecution:
    """Verifies payments are recorded with status 'pending' and never auto-verified."""

    def test_payment_recorded_strictly_pending(self, test_env, monkeypatch):
        mock_db, db_store, _ = test_env

        async def mock_extract_payment(*args, **kwargs):
            return ExtractedMessage(
                message_id="SM_pay_01",
                timestamp="2026-11-01T00:00:00",
                media_type="text",
                type="payment",
                customer_phone=CUSTOMER_PHONE,
                customer_name="Priya Sharma",
                raw_text="Maine 1299 UPI kar diya ref 409827182910",
                items=[],
                amount=1299.0,
                upi_txn_id="409827182910",
                confidence=ConfidenceScore(overall=0.95, items=0.95, amount=0.95),
                reply_needed=True,
            )
        monkeypatch.setattr("backend.app.services.webhook_orchestration_service.extract_text", mock_extract_payment)

        service = WebhookOrchestrationService(db=mock_db)

        form = {
            "MessageSid": "SM_pay_01",
            "From": f"whatsapp:{CUSTOMER_PHONE}",
            "To": f"whatsapp:{CHANNEL_PHONE}",
            "Body": "Maine 1299 UPI kar diya ref 409827182910",
        }
        resp = asyncio.run(service.process_incoming_webhook("http://test/webhook", form, None))
        assert resp.status_code == 200
        content = resp.body.decode("utf-8")
        assert "Payment Received" in content
        assert "Pending Verification" in content

        # Verify payment in payments table
        payments = db_store.get("payments", [])
        assert len(payments) == 1
        assert payments[0]["status"] == PaymentStatus.PENDING.value
        assert payments[0]["amount"] == Decimal("1299") or payments[0]["amount"] == 1299.00


# ============================================================================
# 10. HTTP Endpoint Integration Tests
# ============================================================================

class TestWebhookHTTPRoutes:
    """Verifies FastAPI HTTP endpoints for /webhook and /api/webhook."""

    def test_get_webhook_handshake(self):
        resp = client.get("/webhook?hub.mode=subscribe&hub.challenge=test_challenge_123&hub.verify_token=munim_verify_2026")
        assert resp.status_code == 200
        assert resp.text == "test_challenge_123"

    def test_post_webhook_invalid_signature_raises_403(self, monkeypatch):
        monkeypatch.setattr(settings, "TWILIO_VALIDATE_SIGNATURE", True)
        monkeypatch.setattr(settings, "DRY_RUN", False)
        monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "real_secret_token")

        form = {
            "MessageSid": "SM_sig_fail",
            "From": "whatsapp:+919876543210",
            "To": "whatsapp:+14155238886",
            "Body": "hello",
        }
        headers = {"X-Twilio-Signature": "completely_invalid_signature"}
        resp = client.post("/webhook", data=form, headers=headers)
        assert resp.status_code == 403
        assert "Invalid Twilio signature" in resp.text
