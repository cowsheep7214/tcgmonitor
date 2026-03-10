# alerts/sms_alert.py
# ─────────────────────────────────────────────
# Sends SMS alerts via Twilio
# pip install twilio
# ─────────────────────────────────────────────

import logging
from config.config import (
    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER, ALERT_PHONE_NUMBERS
)

logger = logging.getLogger(__name__)


def send_sms(result: dict) -> bool:
    """Send an SMS alert for a stock hit to all configured numbers."""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
        logger.warning("Twilio credentials not configured – skipping SMS")
        return False

    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        price_str = f"${result['price']}" if result.get("price") else "retail"
        msg = (
            f"🃏 TCG STOCK ALERT\n"
            f"{result['product']}\n"
            f"📍 {result['retailer']} – {result.get('store', 'Online')}\n"
            f"💰 {price_str}\n"
            f"🔗 {result.get('url', '')}\n"
            f"Buy for yourself, leave some for others! 💙"
        )

        success = True
        for number in ALERT_PHONE_NUMBERS:
            number = number.strip()
            if not number:
                continue
            try:
                client.messages.create(
                    body=msg,
                    from_=TWILIO_FROM_NUMBER,
                    to=number
                )
                logger.info(f"[SMS] Alert sent to {number}")
            except Exception as e:
                logger.error(f"[SMS] Failed to send to {number}: {e}")
                success = False

        return success

    except ImportError:
        logger.error("[SMS] twilio package not installed. Run: pip install twilio")
        return False
    except Exception as e:
        logger.error(f"[SMS] Unexpected error: {e}")
        return False
