# monitors/target_monitor.py
# ─────────────────────────────────────────────
# Queries Target's public Redsky availability API
# ─────────────────────────────────────────────

import requests
import logging
from config.config import HEADERS, DEFAULT_ZIP

logger = logging.getLogger(__name__)

# Target's public store-availability endpoint (same one powering their website)
REDSKY_URL = (
    "https://redsky.target.com/redsky_aggregations/v1/web/"
    "pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96"
    "&tcin={tcin}&pricing_store_id={store_id}&visitor_id=anonymous"
)

STORE_SEARCH_URL = (
    "https://redsky.target.com/v3/stores/nearby/{zip}?"
    "key=9f36aeafbe60771e321a7cc95a78140772ab3e96&limit=10&within=25&unit=mile"
)


def get_nearby_store_ids(zip_code: str = DEFAULT_ZIP) -> list[dict]:
    """Return list of {store_id, name, city} for stores near zip_code."""
    try:
        r = requests.get(STORE_SEARCH_URL.format(zip=zip_code), headers=HEADERS, timeout=10)
        r.raise_for_status()
        stores = r.json().get("locations", [])
        return [
            {
                "store_id": s["location_id"],
                "name": s.get("location_name", "Target"),
                "city": s.get("city", ""),
            }
            for s in stores
        ]
    except Exception as e:
        logger.error(f"[Target] Failed to fetch stores: {e}")
        return []


def check_product(product: dict, zip_code: str = DEFAULT_ZIP) -> list[dict]:
    """
    Check stock for a product at nearby Target stores.
    Returns list of in-stock results: [{store, product, url, qty_hint}]
    """
    tcin = product.get("tcin")
    if not tcin:
        return []

    results = []
    stores = get_nearby_store_ids(zip_code)

    for store in stores:
        try:
            url = REDSKY_URL.format(tcin=tcin, store_id=store["store_id"])
            r = requests.get(url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()

            fulfillment = (
                data.get("data", {})
                    .get("product", {})
                    .get("fulfillment", {})
            )
            store_opts = fulfillment.get("store_options", [])

            for opt in store_opts:
                avail = opt.get("order_pickup", {}).get("availability_status", "")
                if avail in ("IN_STOCK", "LIMITED_STOCK"):
                    qty = opt.get("order_pickup", {}).get("available_to_promise_quantity", "?")
                    results.append({
                        "retailer": "Target",
                        "store": f"{store['name']} – {store['city']}",
                        "product": product["name"],
                        "status": avail,
                        "qty_hint": qty,
                        "url": f"https://www.target.com/p/-/A-{tcin}",
                        "price": None,  # fetched separately if needed
                    })
        except Exception as e:
            logger.debug(f"[Target] Error checking {product['name']} @ store {store['store_id']}: {e}")

    return results
