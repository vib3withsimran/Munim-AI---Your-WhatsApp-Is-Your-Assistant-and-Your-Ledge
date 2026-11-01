import base64
import json
import logging
import httpx
from typing import Optional, Dict, Any, List

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

GEMINI_MODELS_FALLBACK = [
    settings.GEMINI_MODEL,
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-3.1-flash-lite"
]

async def call_gemini(
    prompt: str,
    system_instruction: Optional[str] = None,
    media_bytes: Optional[bytes] = None,
    media_mime_type: Optional[str] = None,
    temperature: float = 0.1,
    timeout: float = 12.0
) -> Dict[str, Any]:
    """
    Multimodal caller for Google Gemini API via REST.
    Accepts text prompts along with optional inline audio or image bytes.
    Returns parsed JSON dictionary.
    """
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured.")
        return {}

    # Build parts list
    parts: List[Dict[str, Any]] = []

    # If media (audio or image) is provided, encode as base64 inlineData
    if media_bytes and media_mime_type:
        encoded_media = base64.b64encode(media_bytes).decode("utf-8")
        parts.append({
            "inlineData": {
                "mimeType": media_mime_type,
                "data": encoded_media
            }
        })

    # Add text prompt part
    full_text = prompt
    if system_instruction:
        full_text = f"{system_instruction}\n\nTask:\n{prompt}"

    parts.append({"text": full_text})

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json"
        }
    }

    # Iterate through models with fallback
    for model in GEMINI_MODELS_FALLBACK:
        if not model:
            continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={settings.GEMINI_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        raw_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                        # Clean backticks if any
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        elif raw_text.startswith("```"):
                            raw_text = raw_text[3:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]
                        raw_text = raw_text.strip()

                        try:
                            parsed = json.loads(raw_text)
                            logger.info(f"Gemini generation succeeded with model: {model}")
                            return parsed
                        except json.JSONDecodeError as jde:
                            logger.error(f"Gemini returned invalid JSON ({jde}): {raw_text[:200]}")
                            return {"raw_output": raw_text, "error": "json_decode_error"}
                else:
                    logger.warning(f"Gemini model {model} returned status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini API attempt failed for {model}: {e}")

    logger.error("All Gemini model endpoints failed.")
    return {}

