"""
capture.py

Handles screen capture using mss, with the capture region defined as
PERCENTAGES of screen dimensions so the same config works across
different resolutions (1080p, 1440p, 4K, etc.) as long as Warframe's
UI scale is left at default.

Triggering is HOTKEY-BASED for now (press a key, capture fires) rather
than automatic reward-screen detection — simpler and fully reliable,
at the cost of needing a manual key press each time relics are opened.
Automatic detection can be revisited later as a separate module without
touching this one, since triggering and capturing are kept independent.

Public interface:
    Capturer(config_path).get_full_region_frame() -> numpy array (BGR)
    Capturer(config_path).on_hotkey(callback) -> registers callback,
        called with the captured frame each time the hotkey is pressed
    Capturer(config_path).run_forever() -> blocks, listening for hotkey presses

Config is a plain JSON file (see config/settings.json). Keys starting
with "_comment" are just inline documentation and are ignored when read.
"""

import json
import time
import numpy as np
import mss # type: ignore
import keyboard # type: ignore


class Capturer:
    def __init__(self, config_path="config/settings.json"):
        with open(config_path, "r") as f:
            cfg = json.load(f)["capture"]

        self.monitor_index = cfg["monitor_index"]
        self.region_frac = cfg["region"]
        self.hotkey = cfg["hotkey"]
        self.debounce_seconds = cfg.get("hotkey_debounce_seconds", 0.5)

        self._sct = mss.mss()
        self._monitor = self._sct.monitors[self.monitor_index]

        # Precompute the absolute pixel box from the fractional config,
        # based on this monitor's actual resolution.
        self._region_box = self._frac_to_box(self.region_frac)

        self._last_trigger_time = 0.0

    def _frac_to_box(self, frac):
        """Convert a {left, top, width, height} fraction dict into
        an absolute pixel dict mss can use, relative to the chosen monitor."""
        mon = self._monitor
        return {
            "left": mon["left"] + int(frac["left"] * mon["width"]),
            "top": mon["top"] + int(frac["top"] * mon["height"]),
            "width": int(frac["width"] * mon["width"]),
            "height": int(frac["height"] * mon["height"]),
        }

    def _grab(self, box):
        """Grab a region and return it as a numpy BGR array."""
        raw = self._sct.grab(box)
        # mss gives BGRA; drop alpha channel, keep BGR (OpenCV-friendly order)
        frame = np.array(raw)[:, :, :3]
        return frame

    def get_full_region_frame(self):
        """Capture the full reward-name region (all items at once)."""
        return self._grab(self._region_box)

    def on_hotkey(self, callback):
        """
        Registers `callback(frame)` to be called every time the
        configured hotkey is pressed. Includes a debounce so a single
        physical key press (which can generate multiple OS-level key
        events) doesn't fire multiple captures.
        """
        def _handler():
            now = time.time()
            if now - self._last_trigger_time < self.debounce_seconds:
                return
            self._last_trigger_time = now
            frame = self.get_full_region_frame()
            callback(frame)

        keyboard.add_hotkey(self.hotkey, _handler)

    def run_forever(self):
        """
        Blocks the current thread, listening for hotkey presses.
        Call on_hotkey(...) first to register what happens on trigger.
        Ctrl+C or process exit stops it.
        """
        print(f"Listening for hotkey '{self.hotkey}'... (Ctrl+C to stop)")
        keyboard.wait()


if __name__ == "__main__":
    # Manual test: run this file directly, then press the configured
    # hotkey (default F8) while Warframe is open. Each press saves a
    # fresh capture to debug/captures/ so you can verify the region
    # is aligned and the hotkey is actually being caught.
    import cv2
    import os

    cap = Capturer()
    os.makedirs("debug/captures", exist_ok=True)

    def handle_capture(frame):
        ts = int(time.time())
        out_path = f"debug/captures/capture.png"
        cv2.imwrite(out_path, frame)
        print(f"Captured -> {out_path}")

    cap.on_hotkey(handle_capture)
    cap.run_forever()