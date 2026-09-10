"""
capture.py

Handles screen capture using mss and hotkey detection.
"""

import json
import time
import keyboard  # type: ignore
import mss  # type: ignore
import numpy as np


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
        self.region_box = self._frac_to_box(self.region_frac)
        self._last_trigger_time = 0.0

    def _frac_to_box(self, frac):
        mon = self._monitor
        return {
            "left": mon["left"] + int(frac["left"] * mon["width"]),
            "top": mon["top"] + int(frac["top"] * mon["height"]),
            "width": int(frac["width"] * mon["width"]),
            "height": int(frac["height"] * mon["height"]),
        }

    def _grab(self, box):
        raw = self._sct.grab(box)
        return np.array(raw)[:, :, :3]  # Drop alpha, return BGR

    def get_full_region_frame(self):
        return self._grab(self.region_box)

    def on_hotkey(self, callback):
        def _handler():
            now = time.time()
            if now - self._last_trigger_time < self.debounce_seconds:
                return
            self._last_trigger_time = now
            frame = self.get_full_region_frame()
            callback(frame)

        keyboard.add_hotkey(self.hotkey, _handler)

    def run_forever(self):
        print(f"Listening for hotkey '{self.hotkey}'... (Press Ctrl+C to exit)")
        keyboard.wait()