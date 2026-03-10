# 🃏 TCG Fair-Access Stock Monitor

> **Mission:** Help real fans buy trading cards at retail price — not scalpers.
> Built for true collectors of Pokémon TCG, One Piece TCG, and Dragon Ball TCG.

---

## What it does
- Polls **Target, Walmart, GameStop, Best Buy, and Barnes & Noble** for stock
- Sends **Discord webhook** embeds when stock is detected
- Sends **SMS via Twilio** to registered numbers
- Hosts a **web dashboard** to view alert history

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set environment variables
Create a `.env` file (or export these in your shell):

```bash
# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL

# Twilio SMS (optional)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+15551234567
ALERT_PHONE_NUMBERS=+15559876543,+15551112222   # comma-separated

# Your ZIP code for store searches
DEFAULT_ZIP=78701
```

### 3. Add/edit products
Open `config/config.py` and update the `PRODUCTS` list with the TCINs,
UPCs, and SKUs for the specific sets you want to track.

Finding TCINs:
- **Target TCIN**: visible in the URL on target.com  
  e.g. `target.com/p/pokemon-box/-/A-87978831` → TCIN is `87978831`
- **Walmart item ID**: visible in the URL on walmart.com  
  e.g. `walmart.com/ip/pokemon-box/4716533165` → ID is `4716533165`
- **GameStop slug**: the URL path on gamestop.com after `/products/`

### 4. Run the monitor
```bash
python main.py
```

### 5. Run the web dashboard (separate terminal)
```bash
python dashboard/app.py
# Open http://localhost:5000
```

---

## Project structure
```
tcg-monitor/
├── main.py                  # Main polling loop
├── requirements.txt
├── config/
│   └── config.py            # All settings + product list
├── monitors/
│   ├── target_monitor.py    # Target Redsky API
│   ├── walmart_monitor.py   # Walmart availability
│   ├── gamestop_monitor.py  # GameStop scraper
│   ├── bestbuy_monitor.py   # Best Buy API
│   └── barnesnoble_monitor.py
├── alerts/
│   ├── discord_alert.py     # Discord webhook embeds
│   └── sms_alert.py         # Twilio SMS
├── data/
│   ├── stock_history.py     # Dedup + alert history
│   └── seen_alerts.json     # Auto-generated at runtime
└── dashboard/
    └── app.py               # Flask web dashboard
```

---

## Adding a new product
In `config/config.py`, add to the `PRODUCTS` list:
```python
{
    "name": "Pokémon Twilight Masquerade Booster Box",
    "brand": "Pokemon",          # Pokemon | OnePiece | DragonBall
    "tcin": "YOUR_TARGET_TCIN",
    "upc":  "YOUR_UPC",
    "walmart_item_id": "YOUR_WALMART_ID",
    "gamestop_sku": "your-gamestop-slug",
    "bestbuy_sku": "YOUR_BESTBUY_SKU",
},
```

---

## Ethics & usage policy
This tool is built for **true fans** who want to buy 1-2 packs for personal use.

- ✅ Personal collection purchases
- ✅ Alerting community members to fair retail access
- ❌ Auto-checkout / bulk purchasing
- ❌ Coordinating reselling
- ❌ Bypassing purchase limits

Every Discord alert includes a reminder: *"Buy only what you need. Leave some for other fans."*

---

## Discord setup
1. In your Discord server, go to **Channel Settings → Integrations → Webhooks**
2. Click **New Webhook**, name it "TCG Stock Bot"
3. Copy the webhook URL into your `.env` as `DISCORD_WEBHOOK_URL`
