import httpx
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

async def send_whatsapp_message(to_phone: str, text: str) -> dict:
    """
    Sends a WhatsApp message using Twilio REST API (with DRY_RUN support).
    """
    clean_phone = to_phone.replace("+", "").replace(" ", "").replace("-", "")

    # DRY RUN mode: useful during local development/testing without consuming credits
    if settings.DRY_RUN:
        print(f"\n[DRY RUN WHATSAPP OUTBOUND] 📲 To +{clean_phone}:\n{text}\n" + "-"*50)
        return {"status": "dry_run_success", "recipient": clean_phone}

    # Ensure Twilio WhatsApp format: 'whatsapp:+<number>'
    recipient_whatsapp = f"whatsapp:+{clean_phone}"
    sender_whatsapp = settings.TWILIO_WHATSAPP_NUMBER
    if not sender_whatsapp.startswith("whatsapp:"):
        sender_whatsapp = f"whatsapp:{sender_whatsapp}"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
    
    auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    data = {
        "From": sender_whatsapp,
        "To": recipient_whatsapp,
        "Body": text
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, data=data, auth=auth)
            response_data = response.json()
            if response.status_code >= 400:
                logger.error(f"Twilio API Error ({response.status_code}): {response_data}")
            else:
                logger.info(f"Twilio WhatsApp message sent to {recipient_whatsapp}: SID {response_data.get('sid')}")
            return response_data
    except Exception as e:
        logger.error(f"Failed to send Twilio WhatsApp message to {recipient_whatsapp}: {e}")
        return {"error": str(e)}
