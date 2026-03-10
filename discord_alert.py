# alerts/discord_alert.py
# ─────────────────────────────────────────────
# Sends rich embed alerts to a Discord webhook
# ─────────────────────────────────────────────

import requests
import logging
from datetime import datetime, timezone
from config.config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

RETAILER_COLORS = {
    "Target":          0xCC0000,   # Target red
    "Walmart":         0x0071CE,   # Walmart blue
    "GameStop":        0xE31937,   # GameStop red
    "Best Buy":        0xFFE000,   # Best Buy yellow
    "Barnes & Noble":  0x1D6F2B,   # B&N green
}

BRAND_THUMBNAILS = {
    "Pokemon":    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Pok%C3%A9mon_Trading_Card_Game_logo.svg/240px-Pok%C3%A9mon_Trading_Card_Game_logo.svg.png",
    "OnePiece":   "https://upload.wikimedia.org/wikipedia/en/9/90/One_Piece_logo.svg",
    "DragonBall": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Dragon_Ball_Z_Logo.svg/240px-Dragon_Ball_Z_Logo.svg.png",
}


def send_alert(result: dict, brand: str = "Pokemon") -> bool:
    """
    Post a Discord embed for a stock hit.
    result = {retailer, store, product, status, qty_hint, url, price}
    """
    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL not set – skipping Discord alert")
        return False

    retailer = result.get("retailer", "Unknown")
    color = RETAILER_COLORS.get(retailer, 0x7289DA)
    thumb = BRAND_THUMBNAILS.get(brand, "")

    price_str = f"${result['price']}" if result.get("price") else "Check site"
    qty_str   = str(result.get("qty_hint", "?"))
    status_emoji = "🟢" if result.get("status") == "IN_STOCK" else "🟡"

    embed = {
        "title": f"{status_emoji}  IN STOCK – {result['product']}",
        "url":   result.get("url", ""),
        "color": color,
        "description": (
            f"**Retailer:** {retailer}\n"
            f"**Location:** {result.get('store', 'Online')}\n"
            f"**Price:** {price_str}\n"
            f"**Qty hint:** {qty_str}\n\n"
            f"🛒 [Buy now — for your personal collection!]({result.get('url', '')})\n\n"
            f"_Remember: buy only what you need. Leave some for other fans! 💙_"
        ),
        "thumbnail": {"url": thumb},
        "footer": {
            "text": "TCG Fair-Access Monitor • For true fans, by true fans",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = {
        "username":   "TCG Stock Bot 🃏",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Pok%C3%A9mon_Trading_Card_Game_logo.svg/240px-Pok%C3%A9mon_Trading_Card_Game_logo.svg.png",
        "embeds":     [embed],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
        logger.info(f"[Discord] Alert sent: {result['product']} @ {retailer}")
        return True
    except Exception as e:
        logger.error(f"[Discord] Failed to send alert: {e}")
        return False


def send_heartbeat(stats: dict) -> None:
    """Send a periodic heartbeat embed so users know the bot is alive."""
    if not DISCORD_WEBHOOK_URL:
        return
    embed = {
        "title": "💓 Bot Heartbeat",
        "color": 0x57F287,
        "description": (
            f"**Products monitored:** {stats.get('products', 0)}\n"
            f"**Retailers active:** {stats.get('retailers', 0)}\n"
            f"**Alerts sent today:** {stats.get('alerts_today', 0)}\n"
            f"**Last check:** {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
        ),
        "footer": {"text": "TCG Fair-Access Monitor"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"username": "TCG Stock Bot 🃏", "embeds": [embed]}, timeout=10)
    except Exception:
        pass
