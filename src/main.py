import re
import sys
import os
import threading
import traceback
from rapidfuzz import fuzz, process  # type: ignore

from capture import Capturer
from extract import get_preprocessed_items, extract_text
from market_api import fetch_item_list, get_market_data
from overlay import Overlay

FORMA_VARIANTS = ["Forma Blueprint", "2x Forma Blueprint", "3x Forma Blueprint"]


def match_name(raw_text, item_list):
    if not raw_text or not item_list:
        return "Unknown Item", 0.0
    clean_query = " ".join(re.sub(r'[^a-zA-Z0-9\s]', ' ', raw_text).split()).lower()
    match, score, _ = process.extractOne(clean_query, item_list, scorer=fuzz.WRatio, processor=lambda s: s.lower())
    return (match, score)


def process_relic_drops(frame, item_list, overlay):
    items = get_preprocessed_items(frame)

    slots = []
    for item_img in items:
        raw_text = extract_text(item_img).lower()
        matched_name, confidence = match_name(raw_text, item_list)
        print(f"Raw OCR: {raw_text!r} -> Matched: {matched_name!r} ({confidence:.1f}%)")

        data = get_market_data(matched_name) if confidence >= 60 else None
        tradable = bool(data and data["tradable"])
        price_line = f"{data['sell_median']}p / top {data['sell_top']}p" if tradable else ""

        slots.append({
            "name": matched_name if confidence >= 60 else "Unknown",
            "price_line": price_line, "tradable": tradable,
        })

    overlay.show_items(slots)


def main():
    item_list = fetch_item_list()
    item_list.extend(v for v in FORMA_VARIANTS if v not in item_list)
    print(f"Loaded {len(item_list)} items." if item_list else "[WARNING] Item list empty.")

    capturer = Capturer()
    overlay = Overlay(capturer.region_box)

    capturer.on_hotkey(lambda frame: process_relic_drops(frame, item_list, overlay))
    threading.Thread(target=capturer.run_forever, daemon=True).start()

    overlay.start()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
        log_path = os.path.join(log_dir, "crash_log.txt")
        with open(log_path, "w") as f:
            f.write(traceback.format_exc())
        print(f"Crashed. Details written to {log_path}")
        input("Press Enter to exit...")