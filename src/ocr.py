"""
ocr.py

Thin wrapper around `winocr` (Windows' built-in OCR engine). Kept
deliberately simple: image in, text out. This isolation means the
OCR backend could be swapped later (e.g. for RapidOCR on non-Windows
setups) without touching capture.py, preprocess.py, or matcher.py.

NOTE: This module only runs on Windows, since winocr wraps a Windows
Runtime API. It cannot be tested/run in a non-Windows environment.

Public interface:
    recognize_text(image_bgr_or_gray) -> str
"""

from winocr import recognize_cv2_sync # type: ignore


def recognize_text(image):
    """
    Runs OCR on a single image (expects one item's cleaned name text,
    e.g. output of preprocess.preprocess_frame). Returns the raw
    recognized text as a single string (may include line breaks for
    wrapped two-line names).

    `recognize_cv2_sync` handles the async Windows Runtime call
    internally, so this stays a plain synchronous function from the
    caller's perspective.
    """
    result = recognize_cv2_sync(image)
    return result["text"].strip()


if __name__ == "__main__":
    # Manual test: run against saved per-item images produced by
    # preprocess.py's test block (debug/captures/item_N_clean.png).
    # Only works on Windows.
    import glob
    import os
    import cv2

    paths = sorted(glob.glob("debug/captures/item_*_clean.png"))
    if not paths:
        print("No cleaned item images found in debug/captures/.")
        print("Run 'python src/preprocess.py <capture>' first.")
    else:
        for path in paths:
            img = cv2.imread(path)
            text = recognize_text(img)
            print(f"{os.path.basename(path)} -> {text!r}")