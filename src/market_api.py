import requests
from statistics import median

API = "https://api.warframe.market/v2"
HEADERS = {
    "User-Agent": "WarframeFuzzyMatcher/1.0",
    "Accept": "application/json",
    "Language": "en",
    "Platform": "pc",
}

# Relic rewards that exist in-game but can't be traded, so there's no
# point (and often no data) hitting the orders endpoint for them.
# Credits/Endo drops have variable amounts in their name (e.g. "5,000
# Credits Cache", "200 Endo"), so those are matched by keyword rather
# than an exact, ever-growing list of every denomination.
NON_TRADABLE_EXACT = {"forma blueprint", "2x forma blueprint", "3x forma blueprint"}
NON_TRADABLE_KEYWORDS = ["credits cache", "endo"]


def _is_non_tradable(item_name):
    name = item_name.lower()
    return name in NON_TRADABLE_EXACT or any(kw in name for kw in NON_TRADABLE_KEYWORDS)


def _title_of(item):
    i18n_en = item.get("i18n", {}).get("en", {}) or {}
    return i18n_en.get("title") or i18n_en.get("name") or item.get("title") or item.get("item_name")


def fetch_market_items():
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
        if title and isinstance(title, str):
            lookup[title.lower()] = item

    return lookup


def get_market_data(item_name, lookup):
    item = lookup.get(item_name.lower())
    if not item:
        return None

    if _is_non_tradable(item_name):
        return {"item": item_name, "non_tradable": True}

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
        "non_tradable": False,
        "sell_median": sell_median,
        "sell_top": sell_top,
        "buy_median": buy_median,
        "buy_top": buy_top,
    }


ITEM_LOOKUP = fetch_market_items()

# FIXED: Appending entries to dictionary using key-value assignments
non_tradable_custom = [
    "forma blueprint",
    "2x forma blueprint",
    "3x forma blueprint",
]

for name in non_tradable_custom:
    if name not in ITEM_LOOKUP:
        # Store a lightweight placeholder object for non-tradables
        ITEM_LOOKUP[name] = {"slug": name, "title": name.title()}

if __name__ == "__main__":
    print(f"Loaded {len(ITEM_LOOKUP)} items from Warframe Market.")