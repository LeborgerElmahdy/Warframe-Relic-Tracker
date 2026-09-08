"""
preprocess.py

Splits a captured reward-row image into per-item column bounds (via gold
color detection), then cleans the FULL frame once via CLAHE + brightness
thresholding and crops per-item images out of that single result --
cheaper than reprocessing each item separately, and keeps shared contrast
context across the whole row.
"""

import cv2
import numpy as np

GOLD_HSV_LOWER = np.array([12, 35, 90])
GOLD_HSV_UPPER = np.array([40, 255, 255])

MIN_TEXT_PIXELS_PER_COL = 200   # column counts as "text" above this gold-pixel count
MIN_TEXT_SPIKE_WIDTH = 4         # narrower true-runs are noise, not real strokes
WORD_GAP_BRIDGE_WIDTH = 15       # gaps up to this wide are spacing within one name
MIN_ITEM_SEGMENT_WIDTH = 20      # segments narrower than this are discarded
SEGMENT_PADDING = 5              # extra pixels kept around each detected segment

UPSCALE_FACTOR = 2.5


def _remove_short_runs(arr, min_width, target_value):
    """Flip runs of `target_value` shorter than `min_width` to the opposite
    value. Used to drop noise spikes (target_value=True) and to bridge
    small gaps between words in the same name (target_value=False)."""
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
    """Returns horizontal (x1, x2) bounds for each item, at original (1x) scale."""
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
    """Upscale -> grayscale -> CLAHE contrast boost -> normalize -> hard
    brightness threshold -> invert to black-on-white. Isolates bright
    letter highlights rather than gold hue, which holds up better against
    icon-edge color bleed."""
    scaled = cv2.resize(frame, None, fx=UPSCALE_FACTOR, fy=UPSCALE_FACTOR,
                         interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=50.0, tileGridSize=(2, 2))
    enhanced = clahe.apply(gray)
    normalized = cv2.normalize(enhanced, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    _, thresholded = cv2.threshold(normalized, 230, 255, cv2.THRESH_BINARY)
    return cv2.bitwise_not(thresholded)


def get_preprocessed_items(frame):
    """Cleans the full frame once, then crops out each item's region
    (scaling item bounds up to match the cleaned image's resolution)."""
    bounds = find_item_segments(frame)
    clean_full = preprocess_frame(frame)

    return [
        clean_full[:, int(x1 * UPSCALE_FACTOR):int(x2 * UPSCALE_FACTOR)]
        for x1, x2 in bounds
    ]