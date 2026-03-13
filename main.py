# main.py — TCG Fair-Access Stock Monitor
import time, logging, sys, os, json, requests, random
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import config as cfg

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "seen_alerts.json")

# ════════════════════════════════════════════════
# HISTORY (dedup)
# ════════════════════════════════════════════════
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w") as f: json.dump(data, f, indent=2)

def is_new(result):
    data = load_history()
    key = f"{result['retailer']}|{result.get('store','')}|{result['product']}"
    last = data.get(key)
    if last is None: return True
    return (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() > 7200

def mark_seen(result):
    data = load_history()
    key = f"{result['retailer']}|{result.get('store','')}|{result['product']}"
    data[key] = datetime.now(timezone.utc).isoformat()
    save_history(data)

# ════════════════════════════════════════════════
# DISCORD
# ════════════════════════════════════════════════
RETAILER_COLORS = {"Target": 0xCC0000}

def send_discord_alert(result):
    if not cfg.DISCORD_WEBHOOK_URL:
        logger.warning("No Discord webhook set!")
        return
    color = RETAILER_COLORS.get(result.get("retailer",""), 0x7289DA)
    price_str  = f"${result['price']}"  if result.get("price") else "Check site"
    qty_str    = f"{int(result['qty'])} in stock" if result.get("qty") else "In stock"

    embed = {
        "title": f"🟢 IN STOCK – {result['product']}",
        "url":   result.get("url",""),
        "color": color,
        "description": (
            f"**Retailer:** {result.get('retailer','?')}\n"
            f"**Store:** {result.get('store','?')}\n"
            f"**Price:** {price_str}\n"
            f"**Quantity:** {qty_str}\n\n"
            f"🛒 [Buy now — for your personal collection!]({result.get('url','')})\n\n"
            f"_Buy only what you need. Leave some for other fans! 💙_"
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer":    {"text": "TCG Fair-Access Monitor • For true fans, by true fans"}
    }
    try:
        r = requests.post(cfg.DISCORD_WEBHOOK_URL,
            json={"username":"TCG Stock Bot 🃏","embeds":[embed]}, timeout=10)
        r.raise_for_status()
        logger.info(f"✅ Discord alert sent for {result['product']} @ {result['store']}")
    except Exception as e:
        logger.error(f"Discord failed: {e}")

# ════════════════════════════════════════════════
# TARGET MONITOR — batched (all TCINs per store in 1 request)
# ════════════════════════════════════════════════
AUSTIN_TARGET_ZIPS = {
    "78702": ("3342", "Austin Saltillo"),
    "78705": ("3250", "Austin UT Campus"),
    "78704": ("96",   "Austin South Lamar"),
    "78723": ("1542", "Austin East"),
    "78749": ("1061", "Austin SW"),
    "78758": ("95",   "Austin North"),
    "78748": ("2288", "Austin Southpark"),
    "78759": ("2409", "Austin Arboretum"),
    "78730": ("1953", "Four Points"),
    "78738": ("1812", "Bee Cave"),
    "78717": ("1797", "Lakeline Mall"),
    "78664": ("1066", "Round Rock"),
    "78660": ("2495", "Pflugerville"),
    "78613": ("2342", "Cedar Park"),
    "78640": ("2725", "Kyle"),
    "78628": ("1982", "Georgetown"),
}

# Build a TCIN -> product name lookup
def build_tcin_map():
    return {p["tcin"]: p for p in cfg.PRODUCTS}

def check_target_all_stores():
    """
    1 request per store (all TCINs batched) = 16 requests per cycle instead of 64.
    """
    tcin_map = build_tcin_map()
    tcins_str = ",".join(tcin_map.keys())
    results = []

    for zip_code, (store_id, store_label) in AUSTIN_TARGET_ZIPS.items():
        try:
            url = (
                f"https://redsky.target.com/redsky_aggregations/v1/web/"
                f"product_summary_with_fulfillment_v1"
                f"?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
                f"&tcins={tcins_str}"
                f"&store_id={store_id}"
                f"&zip={zip_code}"
            )
            r = requests.get(url, headers=cfg.HEADERS, timeout=10)
            time.sleep(random.uniform(3, 7))
            if r.status_code != 200:
                continue

            summaries = r.json().get("data", {}).get("product_summaries", [])
            for s in summaries:
                tcin = str(s.get("tcin", ""))
                product = tcin_map.get(tcin)
                if not product:
                    continue

                fulfillment = s.get("fulfillment", {})
                store_opts  = fulfillment.get("store_options", [])

                for opt in store_opts:
                    in_store_status = opt.get("in_store_only", {}).get("availability_status", "")
                    pickup_status   = opt.get("order_pickup", {}).get("availability_status", "")
                    qty             = opt.get("location_available_to_promise_quantity", 0)
                    store_name      = opt.get("store", {}).get("location_name", store_label)

                    is_available = in_store_status == "IN_STOCK" or pickup_status in ("IN_STOCK", "LIMITED_STOCK")

                    if is_available and qty > 0:
                        logger.info(f"🎯 [{store_name}] {product['name']}: {int(qty)} in stock!")
                        results.append({
                            "retailer": "Target",
                            "store":    f"Target {store_name} (Store #{store_id})",
                            "product":  product["name"],
                            "status":   "IN_STOCK",
                            "qty":      qty,
                            "price":    None,
                            "url":      f"https://www.target.com/p/-/A-{tcin}",
                        })

        except Exception as e:
            logger.debug(f"[Target] Store {store_id} error: {e}")

    return results

# ════════════════════════════════════════════════
# MAIN LOOP
# ════════════════════════════════════════════════
def main():
    logger.info("🃏 TCG Fair-Access Monitor starting up!")
    logger.info(f"   Tracking {len(cfg.PRODUCTS)} products")
    logger.info(f"   Checking {len(AUSTIN_TARGET_ZIPS)} Austin Target stores")
    logger.info(f"   ZIP: {cfg.DEFAULT_ZIP} | Every {cfg.POLL_INTERVAL}s")
    logger.info("   Press Ctrl+C to stop\n")

    if cfg.DISCORD_WEBHOOK_URL:
        try:
            requests.post(cfg.DISCORD_WEBHOOK_URL, json={
                "username": "TCG Stock Bot 🃏",
                "content": (
                    f"✅ **Bot started!** Monitoring **{len(cfg.PRODUCTS)} products** "
                    f"across **{len(AUSTIN_TARGET_ZIPS)} Austin Target stores**. "
                    f"Checking every {cfg.POLL_INTERVAL}s. 🎯"
                )
            }, timeout=10)
        except: pass

    while True:
        logger.info(f"⏱  Checking stock… {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
        found_any = False

        if cfg.ENABLED_RETAILERS.get("target", False):
            try:
                hits = check_target_all_stores()
                for hit in hits:
                    if is_new(hit):
                        found_any = True
                        mark_seen(hit)
                        logger.info(f"🚨 ALERT SENT: {hit['product']} @ {hit['store']} ({int(hit.get('qty',0))} in stock)")
                        send_discord_alert(hit)
            except Exception as e:
                logger.error(f"Error checking Target: {e}")

        if not found_any:
            logger.info("😴 No new stock this round.\n")

        try:
            time.sleep(cfg.POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("👋 Monitor stopped. Bye!")
            break

if __name__ == "__main__":
    main()
