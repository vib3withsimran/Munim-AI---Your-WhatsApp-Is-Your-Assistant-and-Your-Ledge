import base64
import hashlib
import hmac
import logging
from typing import Dict, Mapping, Optional, Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def compute_twilio_signature(url: str, params: Mapping[str, Any], auth_token: str) -> str:
    """
    Computes Twilio HMAC-SHA1 signature according to Twilio's official specification:
    1. Start with the full request URL.
    2. Sort POST parameter keys alphabetically in ascending order.
    3. For each key, append the key and its value to the URL (without delimiters).
    4. Compute HMAC-SHA1 of the resulting string using auth_token as the secret key.
    5. Base64-encode the digest.
    """
    # Sort parameter keys alphabetically
    sorted_keys = sorted(params.keys())
    data = url + "".join(f"{k}{params[k]}" for k in sorted_keys)

    mac = hmac.new(
        key=auth_token.encode("utf-8"),
        msg=data.encode("utf-8"),
        digestmod=hashlib.sha1,
    )
    return base64.b64encode(mac.digest()).decode("utf-8")


def validate_twilio_signature(
    url: str,
    params: Mapping[str, Any],
    signature: Optional[str],
    auth_token: Optional[str] = None,
) -> bool:
    """
    Validates incoming Twilio webhook signature header (X-Twilio-Signature).
    
    Safety and Environment Rules:
    - If settings.TWILIO_VALIDATE_SIGNATURE is False, returns True (allows bypassing in dev/test).
    - If settings.DRY_RUN is True, returns True.
    - If signature is None or empty when validation is enabled, returns False.
    - Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    """
    if not settings.TWILIO_VALIDATE_SIGNATURE:
        return True

    if settings.DRY_RUN:
        return True

    token = auth_token or settings.TWILIO_AUTH_TOKEN
    if not token:
        logger.warning("Twilio signature validation enabled but TWILIO_AUTH_TOKEN is not configured.")
        return False

    if not signature:
        logger.warning("Twilio webhook request missing X-Twilio-Signature header.")
        return False

    expected_sig = compute_twilio_signature(url=url, params=params, auth_token=token)
    return hmac.compare_digest(expected_sig, signature)

