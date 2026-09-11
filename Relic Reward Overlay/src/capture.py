import json
import os
import sys
import time
import numpy as np
import mss  # type: ignore
import keyboard # type: ignore


def _resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


class Capturer:
    def __init__(self, config_path=None):
        config_path = config_path or _resource_path("config/settings.json")
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
        return np.array(raw)[:, :, :3]

    def get_full_region_frame(self):
        return self._grab(self.region_box)

    def on_hotkey(self, callback):
        def _handler():
            now = time.time()
            if now - self._last_trigger_time < self.debounce_seconds:
                return
            self._last_trigger_time = now
            callback(self.get_full_region_frame())

        keyboard.add_hotkey(self.hotkey, _handler)

    def run_forever(self):
        print(f"Listening for hotkey '{self.hotkey}'... (Ctrl+C to stop)")
        keyboard.wait()


if __name__ == "__main__":
    import cv2

    cap = Capturer()
    os.makedirs("debug/captures", exist_ok=True)

    def handle_capture(frame):
        ts = int(time.time())
        out_path = f"debug/captures/hotkey_capture_{ts}.png"
        cv2.imwrite(out_path, frame)
        print(f"Captured -> {out_path}")

    cap.on_hotkey(handle_capture)
    cap.run_forever()