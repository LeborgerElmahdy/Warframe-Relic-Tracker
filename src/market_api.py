import requests

API_URL = "https://api.warframe.market/v2/items"

HEADERS = {
    "User-Agent": "WarframeFuzzyMatcher/1.0",
    "Accept": "application/json",
    "Language": "en",
    "Platform": "pc",
}


def fetch_warframe_market_items():
    try:
        response = requests.get(
            API_URL,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        # v2 response:
        # {
        #     "apiVersion": "...",
        #     "data": [...]
        # }
        items = data.get("data", [])

        names = []

        for item in items:
            name = (
                item
                .get("i18n", {})
                .get("en", {})
                .get("name")
            )

            if name:
                names.append(name)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(names))

    except requests.RequestException as e:
        print(f"API error: {e}")

    except (ValueError, TypeError) as e:
        print(f"Invalid API response: {e}")

    return []


# Fetch once
ALL_ITEMS = fetch_warframe_market_items()

print(f"Loaded {len(ALL_ITEMS)} items from Warframe Market.")

# Example:
print(ALL_ITEMS)