import time
import re
from rapidfuzz import fuzz, process # type: ignore

from capture import Capturer
from preprocess import get_preprocessed_items
from ocr import recognize_text
from market_api import ITEM_LOOKUP, get_market_data

def match_name(raw_text):
    if not raw_text or not ITEM_LOOKUP:
        return "Unknown Item", 0.0
    
    clean_query = " ".join(re.sub(r'[^a-zA-Z0-9\s]', ' ', raw_text).split())
    match, score, _ = process.extractOne(clean_query, ITEM_LOOKUP.keys(), scorer=fuzz.WRatio)

    return (match, score)

def process_relic_drops(frame):

    start_time = time.time()

    items = get_preprocessed_items(frame)

    for i, item in enumerate(items):
        raw_text = recognize_text(item).lower()
        matched_key, confidence = match_name(raw_text)

        print(f"  Slot {i + 1}:")
        print(f"    Raw OCR : {raw_text!r}")
        print(f"    Matched : {matched_key!r} ({confidence:.1f}% confidence)")

        prices = get_market_data(matched_key, ITEM_LOOKUP)
        if not prices or "forma" in matched_key:
            print("    Non Tradable Item.")
        else:
            print(f"    Median Price: {prices['sell_median']} Platinum \n    Top Offering: {prices['sell_top']} Platinum")

    print(f"Done in {time.time() - start_time:.2f}s")

def main():
    if not ITEM_LOOKUP:
        print("[WARNING] Warframe Market database is empty. Check internet connectivity.")
    else:
        print(f"Loaded {len(ITEM_LOOKUP)} items into fuzzy matching cache.")

    capturer = Capturer()
    capturer.on_hotkey(process_relic_drops)
    capturer.run_forever()


if __name__ == "__main__":
    main()