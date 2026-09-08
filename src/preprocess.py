"""
preprocess.py

Cleans up a raw captured region before handing it to OCR.
"""

import os
import sys
import cv2
import numpy as np

# Gold/tan reward-text color range (HSV).
GOLD_HSV_LOWER = np.array([12, 35, 90])
GOLD_HSV_UPPER = np.array([40, 255, 255])

# Column-splitting thresholds
MIN_TEXT_PIXELS_PER_COL = 200
MIN_TEXT_SPIKE_WIDTH = 4
WORD_GAP_BRIDGE_WIDTH = 15
MIN_ITEM_SEGMENT_WIDTH = 20
SEGMENT_PADDING = 5


def _remove_short_runs(arr, min_width, target_value):
    arr = arr.copy()
    count, start = 0, 0
    for i in range(len(arr) + 1):
        v = arr[i] if i < len(arr) else (not target_value)
        if v == target_value:
            if count == 0:
                start = i
            count += 1
        else:
            if 0 < count < min_width:
                arr[start:i] = not target_value
            count = 0
    return arr


def find_item_segments(frame_bgr):
    """Calculates horizontal bounding boxes for each item on the raw image."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, GOLD_HSV_LOWER, GOLD_HSV_UPPER)
    is_text = mask.sum(axis=0) >= MIN_TEXT_PIXELS_PER_COL

    cleaned = _remove_short_runs(is_text, MIN_TEXT_SPIKE_WIDTH, target_value=True)
    bridged = _remove_short_runs(cleaned, WORD_GAP_BRIDGE_WIDTH, target_value=False)

    segments, in_seg, start = [], False, 0
    for i, v in enumerate(bridged):
        if v and not in_seg:
            start, in_seg = i, True
        elif not v and in_seg:
            segments.append((start, i))
            in_seg = False
    if in_seg:
        segments.append((start, len(bridged)))

    w = frame_bgr.shape[1]
    return [
        (max(0, x1 - SEGMENT_PADDING), min(w, x2 + SEGMENT_PADDING))
        for x1, x2 in segments
        if (x2 - x1) >= MIN_ITEM_SEGMENT_WIDTH
    ]


def preprocess_frame(frame):
    """Processes the FULL image at once to keep notebook contrast consistency."""
    scaled = cv2.resize(frame, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=50.0, tileGridSize=(2, 2))
    enhanced = clahe.apply(gray)

    normalized = cv2.normalize(enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    _, preprocessed = cv2.threshold(normalized, 230, 255, cv2.THRESH_BINARY)

    output = cv2.bitwise_not(preprocessed)
    return output


def get_preprocessed_items(frame):
    """
    1. Preprocesses the full frame (matching notebook output exactly).
    2. Calculates item column bounds.
    3. Crops the preprocessed output into individual item sub-images.
    """
    # Find column boundaries at original scale
    bounds = find_item_segments(frame)
    
    # Preprocess full frame (which upscales by 2.5x)
    clean_full = preprocess_frame(frame)
    
    # Crop clean image (scaling column bounds by 2.5x to match upscaled frame)
    items = []
    for x1, x2 in bounds:
        x1_scaled = int(x1 * 2.5)
        x2_scaled = int(x2 * 2.5)
        items.append(clean_full[:, x1_scaled:x2_scaled])
        
    return items


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    input_path = args[0] if args else "debug/captures/capture.png"

    if not os.path.exists(input_path):
        print(f"No input image found at '{input_path}'.")
        sys.exit(1)

    frame = cv2.imread(input_path)
    if frame is None:
        print(f"Failed to read image: '{input_path}'")
        sys.exit(1)

    os.makedirs("debug/captures", exist_ok=True)
    
    # Preprocess first, then crop into items
    items = get_preprocessed_items(frame)
    print(f"Detected {len(items)} item segment(s).")

    for i, item_clean in enumerate(items):
        clean_out = f"debug/captures/item_{i}_clean.png"
        cv2.imwrite(clean_out, item_clean)
        print(f"  item {i}: saved {clean_out}")