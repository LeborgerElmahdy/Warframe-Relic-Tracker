import requests
from statistics import median

API = "https://api.warframe.market/v2"
HEADERS = {"User-Agent": "WarframeFuzzyMatcher/1.0", "Accept": "application/json",
           "Language": "en", "Platform": "pc"}

RELIC_KEYWORDS = ["prime", "blueprint", "forma", "harness", "systems", "chassis",
                  "neuroptics", "barrel", "receiver", "stock", "blade", "handle",
                  "grip", "pouch", "stars"]
ESSENTIAL_ITEMS = ["Forma Blueprint", "2x Forma Blueprint", "Ayatan Amber Star", "Ayatan Cyan Star"]


def _title_of(item):
    i18n_en = item.get("i18n", {}).get("en", {}) or {}
    return i18n_en.get("title") or i18n_en.get("name") or item.get("title") or item.get("item_name")


def fetch_market_items():
    """Fetch WFM items, filter to relic-relevant ones, return {lower_name: {slug, i18n}}."""
    try:
        resp = requests.get(f"{API}/items", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch Warframe Market database: {e}")
        return {}

    lookup = {}
    for item in data:
        title = _title_of(item)
        if not title or not isinstance(title, str):
            continue
        if any(kw in title.lower() for kw in RELIC_KEYWORDS) or title in ESSENTIAL_ITEMS:
            lookup[title.lower()] = item

    return lookup


def get_market_data(item_name, lookup):
    item = lookup.get(item_name.lower())
    if not item:
        return None

    try:
        resp = requests.get(f"{API}/orders/item/{item['slug']}/top", headers=HEADERS, timeout=15)
        data = resp.json().get("data", {})
    except requests.RequestException as e:
        print(f"API error: {e}")
        return None

    def summary(orders):
        plats = [o["platinum"] for o in orders]
        return (median(plats) if plats else None, orders[0]["platinum"] if orders else None)

    sell_median, sell_top = summary(data.get("sell", []))
    buy_median, buy_top = summary(data.get("buy", []))

    return {
        "item": item["i18n"]["en"]["name"],
        "sell_median": sell_median, "sell_top": sell_top,
        "buy_median": buy_median, "buy_top": buy_top,
    }


ITEM_LOOKUP = fetch_market_items()

if __name__ == "__main__":
    print(f"Loaded {len(ITEM_LOOKUP)} items from Warframe Market.")