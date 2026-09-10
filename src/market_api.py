import requests # type: ignore
from statistics import median

API = "https://api.warframe.market/v2"
HEADERS = {
    "User-Agent": "WarframeFuzzyMatcher/1.0",
    "Accept": "application/json",
    "Language": "en",
    "Platform": "pc",
}


def _title_of(item):
    i18n_en = item.get("i18n", {}).get("en", {}) or {}
    return i18n_en.get("title") or i18n_en.get("name") or item.get("title") or item.get("item_name")


def fetch_item_list():
    try:
        resp = requests.get(f"{API}/items", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch Warframe Market database: {e}")
        return {}

    return [_title_of(item) for item in data if _title_of(item)]


def get_market_data(item_name):
    if "forma" in item_name.lower():
        return {
            "item": item_name,
            "tradable": False,
            "sell_median": "N/A",
            "sell_top": "N/A",
        }

    item_slug = item_name.replace(" ", "_").lower()
    try:
        resp = requests.get(f"{API}/orders/item/{item_slug}/top", headers=HEADERS, timeout=15)
        data = resp.json().get("data", {})
    except requests.RequestException as e:
        print(f"API error: {e}")
        return None

    def summary(orders):
        plats = [o["platinum"] for o in orders]
        return (median(plats) if plats else None, orders[0]["platinum"] if orders else None)

    sell_median, sell_top = summary(data.get("sell", []))

    return {
        "item": item_name,
        "tradable": True,
        "sell_median": sell_median,
        "sell_top": sell_top,
    }