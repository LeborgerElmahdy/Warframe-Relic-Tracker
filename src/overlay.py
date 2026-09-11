"""
overlay.py

Click-through, always-on-top overlay: one glassy panel per reward slot,
positioned under that slot's card, with a gap below the item-name row
so player-selection names stay visible.
"""

import ctypes
import tkinter as tk

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

KEY_COLOR = "#010101"      # invisible background
PANEL_FILL = "#0b1620"     # dark glassy panel
ACCENT = "#33e6d8"         # cyan accent border/price text
TEXT_MUTED = "#9fb3bd"     # item name
TEXT_DIM = "#5c6b72"       # non-tradable label

PANEL_HEIGHT = 78
PANEL_GAP_BELOW_TEXT = 140   # clears the player-name row under the cards
CORNER = 10
AUTO_HIDE_MS = 15000
BOX_WIDTH = 220
BOX_GAP = 24


def _round_rect(canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    canvas.create_polygon(pts, smooth=True, **kw)


class Overlay:
    def __init__(self, region_box):
        self.center_x = region_box["left"] + region_box["width"] // 2
        self.base_y = region_box["top"] + region_box["height"] + PANEL_GAP_BELOW_TEXT
        self._hide_job = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", KEY_COLOR)
        self.root.configure(bg=KEY_COLOR)

        screen_w = self.root.winfo_screenwidth()
        self.root.geometry(f"{screen_w}x{PANEL_HEIGHT}+0+{self.base_y}")

        self.canvas = tk.Canvas(self.root, width=screen_w, height=PANEL_HEIGHT,
                                 bg=KEY_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.root.update()
        self._make_click_through()

    def _make_click_through(self):
        hwnd = self.root.winfo_id()
        parent = ctypes.windll.user32.GetParent(hwnd)
        target = parent if parent else hwnd
        style = ctypes.windll.user32.GetWindowLongW(target, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(target, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

    def show_items(self, slots):
        """slots: list of {"name", "price_line", "tradable"}. Always drawn
        as uniform, evenly-spaced boxes centered under the reward row,
        regardless of each item's actual detected position/width."""
        self.root.after(0, self._draw, slots)

    def _draw(self, slots):
        if self._hide_job is not None:
            self.root.after_cancel(self._hide_job)

        self.canvas.delete("all")

        n = len(slots)
        total_width = n * BOX_WIDTH + (n - 1) * BOX_GAP
        start_x = self.center_x - total_width // 2

        for i, slot in enumerate(slots):
            x1 = start_x + i * (BOX_WIDTH + BOX_GAP)
            x2 = x1 + BOX_WIDTH
            _round_rect(self.canvas, x1, 4, x2, PANEL_HEIGHT - 4, CORNER,
                        fill=PANEL_FILL, outline=ACCENT, width=1)

            cx = (x1 + x2) // 2
            self.canvas.create_text(cx, 22, text=slot["name"], fill=TEXT_MUTED,
                                     font=("Consolas", 9), width=(BOX_WIDTH - 12))

            if slot["tradable"]:
                self.canvas.create_text(cx, 52, text=slot["price_line"], fill=ACCENT,
                                         font=("Consolas", 12, "bold"))
            else:
                self.canvas.create_text(cx, 52, text="Not tradable", fill=TEXT_DIM,
                                         font=("Consolas", 10, "italic"))

        self._hide_job = self.root.after(AUTO_HIDE_MS, self._clear)

    def _clear(self):
        self.canvas.delete("all")
        self._hide_job = None

    def start(self):
        self._keep_alive()
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.root.destroy()

    def _keep_alive(self):
        # Tkinter's mainloop is a C-level event loop that won't reliably
        # notice Ctrl+C (SIGINT) unless Python code runs periodically.
        # This no-op timer hands control back often enough to catch it.
        self.root.after(200, self._keep_alive)


if __name__ == "__main__":
    fake_region = {"left": 0, "top": 300, "width": 1000, "height": 60}
    ov = Overlay(fake_region)
    ov.show_items([
        {"name": "Braton Prime Blueprint", "price_line": "12p", "tradable": True},
        {"name": "Forma Blueprint", "price_line": "", "tradable": False},
        {"name": "Soma Prime Barrel", "price_line": "25p", "tradable": True},
    ])
    ov.start()