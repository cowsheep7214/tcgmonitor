# monitors/walmart_monitor.py
# ─────────────────────────────────────────────
# Uses Walmart's public item availability endpoint
# ─────────────────────────────────────────────

import requests
import logging
from config.config import HEADERS, DEFAULT_ZIP

logger = logging.getLogger(__name__)

WALMART_API = (
    "https://www.walmart.com/store/ajax/selected-store-product-price-avail"
    "?products={item_id}"
)

STORE_SEARCH_URL = (
    "https://www.walmart.com/store/finder/electrode/api/stores"
    "?singleLineAddr={zip}&distance=25"
)


def get_nearby_store_ids(zip_code: str = DEFAULT_ZIP) -> list[dict]:
    try:
        r = requests.get(STORE_SEARCH_URL.format(zip=zip_code), headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        stores = data.get("payload", {}).get("storesData", {}).get("stores", [])
        return [{"store_id": s["id"], "name": s.get("displayName", "Walmart"), "city": s.get("city", "")} for s in stores[:8]]
    except Exception as e:
        logger.error(f"[Walmart] Store lookup failed: {e}")
        return []


def check_product(product: dict, zip_code: str = DEFAULT_ZIP) -> list[dict]:
    item_id = product.get("walmart_item_id")
    if not item_id:
        return []

    results = []
    stores = get_nearby_store_ids(zip_code)

    for store in stores:
        try:
            headers = {**HEADERS, "x-walmart-store-id": str(store["store_id"])}
            r = requests.get(WALMART_API.format(item_id=item_id), headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()

            items = data.get("payload", {}).get("products", [])
            for item in items:
                avail = item.get("availabilityStatus", "")
                if avail in ("IN_STOCK", "AVAILABLE"):
                    results.append({
                        "retailer": "Walmart",
                        "store": f"{store['name']} – {store['city']}",
                        "product": product["name"],
                        "status": "IN_STOCK",
                        "qty_hint": item.get("quantity", "?"),
                        "url": f"https://www.walmart.com/ip/{item_id}",
                        "price": item.get("priceInfo", {}).get("currentPrice", {}).get("price"),
                    })
        except Exception as e:
            logger.debug(f"[Walmart] Error checking {product['name']}: {e}")

    return results
