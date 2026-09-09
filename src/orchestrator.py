import time
import re
from rapidfuzz import fuzz, process  # type: ignore

from capture import Capturer
from extract import get_preprocessed_items, extract_text
from market_api import fetch_item_list, get_market_data


def match_name(raw_text, item_list):
    if not raw_text or not item_list:
        return "Unknown Item", 0.0

    clean_query = " ".join(re.sub(r'[^a-zA-Z0-9\s]', ' ', raw_text).split()).lower()
    match, score, _ = process.extractOne(clean_query, item_list, scorer=fuzz.WRatio, processor=lambda s: s.lower())

    return (match, score)


def process_relic_drops(frame, item_list):
    start_time = time.time()

    items = get_preprocessed_items(frame)

    for i, item in enumerate(items):
        raw_text = extract_text(item).lower()
        matched_name, confidence = match_name(raw_text, item_list)

        print(f"  Slot {i + 1}:")
        print(f"    Raw OCR : {raw_text!r}")
        print(f"    Matched : {matched_name!r} ({confidence:.1f}% confidence)")

        item_data = get_market_data(matched_name)
        if not item_data:
            print("    Invalid Item")
        elif item_data["tradable"] == False:
            print("    Non Tradable Item.")
        else:
            print(f"    Median Price: {item_data['sell_median']} Platinum \n    Top Offering: {item_data['sell_top']} Platinum")

    print(f"Done in {time.time() - start_time:.2f}s")


def main():
    FORMA_VARIANTS = ["Forma Blueprint", "2x Forma Blueprint", "3x Forma Blueprint"]
    item_list = fetch_item_list()
    item_list.extend(FORMA_VARIANTS)

    if not item_list:
        print("[WARNING] Item List is EMPTY.")
    else:
        print(f"Loaded {len(item_list)} Items into the Item list.")

    capturer = Capturer()
    capturer.on_hotkey(lambda frame: process_relic_drops(frame, item_list))
    capturer.run_forever()


if __name__ == "__main__":
    main()