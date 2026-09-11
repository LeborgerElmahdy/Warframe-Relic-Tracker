import cv2  # type: ignore
import numpy as np  # type: ignore
from winocr import recognize_cv2_sync  # type: ignore

GOLD_HSV_LOWER = np.array([12, 35, 70])
GOLD_HSV_UPPER = np.array([40, 255, 255])

MIN_TEXT_PIXELS_PER_COL = 200
MIN_TEXT_SPIKE_WIDTH = 3
WORD_GAP_BRIDGE_WIDTH = 15
MIN_ITEM_SEGMENT_WIDTH = 20
SEGMENT_PADDING = 5
UPSCALE_FACTOR = 2.5


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
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, GOLD_HSV_LOWER, GOLD_HSV_UPPER)
    is_text = mask.sum(axis=0) >= MIN_TEXT_PIXELS_PER_COL

    cleaned = _remove_short_runs(is_text, MIN_TEXT_SPIKE_WIDTH, True)
    bridged = _remove_short_runs(cleaned, WORD_GAP_BRIDGE_WIDTH, False)

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
        if x2 - x1 >= MIN_ITEM_SEGMENT_WIDTH
    ]


def preprocess_frame(frame):
    scaled = cv2.resize(
        frame, None, fx=UPSCALE_FACTOR, fy=UPSCALE_FACTOR,
        interpolation=cv2.INTER_CUBIC
    )
    hsv = cv2.cvtColor(scaled, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, GOLD_HSV_LOWER, GOLD_HSV_UPPER)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return cv2.bitwise_not(mask)


def get_preprocessed_items(frame):
    bounds = find_item_segments(frame)
    clean_full = preprocess_frame(frame)
    return [
        clean_full[:, int(x1 * UPSCALE_FACTOR):int(x2 * UPSCALE_FACTOR)]
        for x1, x2 in bounds
    ]


def extract_text(image):
    return recognize_cv2_sync(image)["text"].strip()