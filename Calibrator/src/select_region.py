"""
select_region.py

Calibration tool: shows a reference image, lets you drag a rectangle
over it, and saves the selection as resolution-independent fractions
into config/settings.json under capture.<key>.

This script can live ANYWHERE relative to the project -- it searches
upward from its own location for a config/settings.json file rather
than assuming a fixed folder layout.

Usage:
    python select_region.py [key] [image_path]
    e.g. python select_region.py region
         python select_region.py region path\to\my_screenshot.png
         python select_region.py sentinel

If image_path is omitted, defaults to <repo_root>/data/calibration.png.
If that file doesn't exist either, falls back to a live screenshot.
"""

import sys
import os
import json
import tkinter as tk
from PIL import Image, ImageTk
import mss


def find_repo_root(start_dir, max_levels=8):
    """Walks upward from start_dir looking for a config/settings.json,
    so this tool works regardless of which folder it's placed in."""
    current = os.path.abspath(start_dir)
    for _ in range(max_levels):
        if os.path.exists(os.path.join(current, "config", "settings.json")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def load_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)


def save_config(config_path, cfg):
    with open(config_path, "w") as f:
        json.dump(cfg, f, indent=2)


def load_reference_image(image_path, monitor_index):
    """Loads a static PNG from disk if it exists, otherwise falls back
    to a live screenshot. Returns (PIL.Image, (width, height))."""
    if image_path and os.path.exists(image_path):
        img = Image.open(image_path).convert("RGB")
        print(f"Using saved reference image: {image_path}")
        return img, (img.width, img.height)

    print(f"No image found at '{image_path}', taking a live screenshot instead.")
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        raw = sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
        return img, (monitor["width"], monitor["height"])


def select_rectangle(img):
    result = {}
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.config(cursor="crosshair")

    photo = ImageTk.PhotoImage(img)
    canvas = tk.Canvas(root, width=img.width, height=img.height, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=photo, anchor="nw")
    canvas.create_text(img.width // 2, 30, text="Drag to select the region. Esc to cancel.",
                        fill="white", font=("Consolas", 16))

    start = {}
    rect_id = [None]

    def on_press(event):
        start["x"], start["y"] = event.x, event.y
        rect_id[0] = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                              outline="#33e6d8", width=2)

    def on_drag(event):
        canvas.coords(rect_id[0], start["x"], start["y"], event.x, event.y)

    def on_release(event):
        x1, y1, x2, y2 = start["x"], start["y"], event.x, event.y
        result["box"] = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
        root.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", lambda e: root.destroy())

    root.mainloop()
    return result.get("box")


def main():
    key = sys.argv[1] if len(sys.argv) > 1 else "region"

    repo_root = find_repo_root(os.path.dirname(os.path.abspath(__file__)))
    if not repo_root:
        print("Could not find a config/settings.json in any parent folder.")
        print("Make sure this script sits somewhere inside your project.")
        return

    config_path = os.path.join(repo_root, "config", "settings.json")
    default_image_path = os.path.join(repo_root, "data", "calibration.png")
    image_path = sys.argv[2] if len(sys.argv) > 2 else default_image_path

    cfg = load_config(config_path)
    monitor_index = cfg["capture"].get("monitor_index", 1)

    img, (ref_width, ref_height) = load_reference_image(image_path, monitor_index)
    box = select_rectangle(img)
    if not box:
        print("Cancelled, nothing saved.")
        return

    x1, y1, x2, y2 = box
    frac = {
        "left": round(x1 / ref_width, 4),
        "top": round(y1 / ref_height, 4),
        "width": round((x2 - x1) / ref_width, 4),
        "height": round((y2 - y1) / ref_height, 4),
    }

    cfg["capture"][key] = frac
    save_config(config_path, cfg)

    print(f"Saved '{key}' to {config_path}:")
    print(json.dumps(frac, indent=2))


if __name__ == "__main__":
    main()