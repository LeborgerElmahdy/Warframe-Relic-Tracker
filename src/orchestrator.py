"""
main.py

Orchestrates the Warframe Relic Tracker pipeline:
1. Listens for hotkey trigger (from capture.py)
2. Captures screen region
3. Preprocesses capture into individual item images (from preprocess.py)
4. Runs Windows OCR on each cleaned sub-image (from ocr.py)
5. Fuzzy matches raw OCR results against Warframe Market API database
"""

import os
import sys
import time
from rapidfuzz import process, fuzz

# Ensure 'src' is in python path if main.py lives at project root
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from capture import Capturer
from preprocess import get_preprocessed_items
from ocr import recognize_text
from market_api import ALL_ITEMS


def match_item_name(raw_ocr_text: str, candidates: list[str], min_cutoff: float = 50.0):
    """
    Fuzzy matches raw OCR text against the Warframe Market item list.
    Replaces newlines with spaces to handle two-line item names.
    """
    if not raw_ocr_text or not candidates:
        return "Unknown Item", 0.0

    # Clean multi-line OCR output (e.g. "Sevagoth Prime\nNeuroptics Blueprint")
    clean_query = " ".join(raw_ocr_text.split())

    match, score, _ = process.extractOne(
        clean_query,
        candidates,
        scorer=fuzz.token_sort_ratio
    )

    if score >= min_cutoff:
        return match, score
    
    return clean_query, score


def process_relic_screen(frame):
    """Callback function triggered when the capture hotkey is pressed."""
    print("\n" + "=" * 50)
    print("Relic Screen Captured! Processing...")
    start_time = time.time()

    # 1. Preprocess full frame & crop into individual item sub-images
    item_images = get_preprocessed_items(frame)
    print(f"Detected {len(item_images)} reward slot(s).")

    # 2. OCR + Fuzzy Match each item
    for i, item_img in enumerate(item_images):
        raw_text = recognize_text(item_img)
        matched_name, confidence = match_item_name(raw_text, ALL_ITEMS)

        print(f"  Slot {i + 1}:")
        print(f"    Raw OCR : {raw_text!r}")
        print(f"    Matched : {matched_name!r} ({confidence:.1f}% confidence)")

    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.2f}s")
    print("=" * 50 + "\n")


def main():
    if not ALL_ITEMS:
        print("[WARNING] Warframe Market item database is empty. Check internet or API endpoint.")
    else:
        print(f"Loaded {len(ALL_ITEMS)} items into item cache.")

    # Initialize screen capturer
    capturer = Capturer()
    
    # Bind orchestrator callback to hotkey
    capturer.on_hotkey(process_relic_screen)

    # Start main loop
    capturer.run_forever()


if __name__ == "__main__":
    main()