"""
main.py

Main orchestrator: capture -> split -> preprocess -> OCR -> fuzzy match -> price lookup.
"""

import os
import sys
import time
from rapidfuzz import fuzz, process

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from capture import Capturer
from preprocess import get_preprocessed_items
from ocr import recognize_text
from market_api import ITEM_LOOKUP, get_market_data

MIN_MATCH_CONFIDENCE = 80.0


def match_item_name(raw_ocr_text, min_cutoff=MIN_MATCH_CONFIDENCE):
    """Fuzzy-match raw OCR text against known item names (lowercase keys).
    Returns (matched_key_or_raw_text, confidence)."""
    if not raw_ocr_text or not ITEM_LOOKUP:
        return "Unknown Item", 0.0

    clean_query = " ".join(raw_ocr_text.replace("\n", " ").split())
    match, score, _ = process.extractOne(clean_query, ITEM_LOOKUP.keys(), scorer=fuzz.WRatio)

    return (match, score) if score >= min_cutoff else (clean_query, score)


def process_relic_screen(frame):
    print("\n" + "=" * 50)
    print("Relic Screen Captured! Processing...")
    start_time = time.time()

    item_frames = get_preprocessed_items(frame)
    print(f"Detected {len(item_frames)} reward slot(s).")

    for i, item_frame in enumerate(item_frames):
        raw_text = recognize_text(item_frame)
        matched_key, confidence = match_item_name(raw_text)

        if confidence < MIN_MATCH_CONFIDENCE:
            print(f"  Slot {i + 1}: ignored (confidence {confidence:.1f}% < {MIN_MATCH_CONFIDENCE:.0f}%)")
            continue

        print(f"  Slot {i + 1}:")
        print(f"    Raw OCR : {raw_text!r}")
        print(f"    Matched : {matched_key!r} ({confidence:.1f}% confidence)")

        prices = get_market_data(matched_key, ITEM_LOOKUP)
        if prices:
            print(f"    Sell    : median: {prices['sell_median']}, top listing: {prices['sell_top']}")
            print(f"    Buy     : median: {prices['buy_median']}, top listing: {prices['buy_top']}")
        else:
            print("    Prices  : unavailable")

    print(f"Done in {time.time() - start_time:.2f}s")
    print("=" * 50 + "\n")


def main():
    if not ITEM_LOOKUP:
        print("[WARNING] Warframe Market database is empty. Check internet connectivity.")
    else:
        print(f"Loaded {len(ITEM_LOOKUP)} items into fuzzy matching cache.")

    capturer = Capturer()
    capturer.on_hotkey(process_relic_screen)
    capturer.run_forever()


if __name__ == "__main__":
    main()