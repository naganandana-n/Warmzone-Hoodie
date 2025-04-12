import tkinter as tk
import mss
from PIL import Image
import numpy as np
import time
import serial

# ─── CONFIG ────────────────────────────────────────────────────────────────
SERIAL_PORT = "COM3"      # e.g. "COM3" on Windows or "/dev/ttyUSB0" on Linux/macOS
BAUD_RATE   = 115200
NUM_LEDS    = 24
# ──────────────────────────────────────────────────────────────────────────

# ─── GUI FOR LINE SELECTION ──────────────────────────────────────────────

class LineSelector(tk.Tk):
    def __init__(self, num_lines=2):
        super().__init__()
        self.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray11", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.num_lines = num_lines
        self.clicks = []        # list of (x,y) clicks
        self.lines = []         # list of ((x0,y0),(x1,y1)) per line
        self.temp_line = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)

    def on_click(self, event):
        self.clicks.append((event.x, event.y))
        if len(self.clicks) % 2 == 0:
            p0 = self.clicks[-2]
            p1 = self.clicks[-1]
            self.lines.append((p0, p1))
            self.canvas.create_line(*p0, *p1, fill="cyan", width=2)
            if len(self.lines) == self.num_lines:
                self.destroy()

    def on_motion(self, event):
        if len(self.clicks) % 2 == 1:
            p0 = self.clicks[-1]
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(*p0, event.x, event.y, dash=(4,2), fill="cyan")

def select_two_lines():
    app = LineSelector(num_lines=2)
    app.mainloop()
    return app.lines

# ─── SAMPLE‐POINT CALCULATION ─────────────────────────────────────────────

def get_equidistant_points(p0, p1, n):
    x0,y0 = p0; x1,y1 = p1
    return [ (x0 + (x1-x0)*(i/(n-1)), y0 + (y1-y0)*(i/(n-1))) for i in range(n) ]

# ─── SCREEN COLOR EXTRACTION ────────────────────────────────────────────

def sample_colors_at(points):
    colors = []
    with mss.mss() as sct:
        for x,y in points:
            region = {"left": int(x), "top": int(y), "width": 1, "height": 1}
            img = sct.grab(region)
            r,g,b = img.pixel(0,0)
            colors.append((r,g,b))
    return colors

# ─── SERIAL LED OUTPUT ───────────────────────────────────────────────────

class SerialLEDController:
    def __init__(self, port, baud, num_leds):
        self.num_leds = num_leds
        self.ser = serial.Serial(port, baud, timeout=1)
        # give it a moment
        time.sleep(2)

    def send_colors(self, colors):
        """
        colors: list of (R,G,B) tuples, length == num_leds
        """
        if len(colors) != self.num_leds:
            raise ValueError(f"Expected {self.num_leds} colors, got {len(colors)}")
        data = bytearray()
        for (r,g,b) in colors:
            data += bytes((r, g, b))
        self.ser.write(data)

# ─── MAIN LOOP ──────────────────────────────────────────────────────────

def main():
    print("Click to define two lines (4 clicks total)...")
    lines = select_two_lines()

    # compute 24 sample points
    points = []
    for p0,p1 in lines:
        pts = get_equidistant_points(p0, p1, NUM_LEDS // 2)
        points.extend(pts)

    print(f"Sampling {len(points)} points. Opening serial on {SERIAL_PORT}@{BAUD_RATE}...")
    controller = SerialLEDController(SERIAL_PORT, BAUD_RATE, NUM_LEDS)

    try:
        while True:
            cols = sample_colors_at(points)
            controller.send_colors(cols)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        controller.ser.close()

if __name__ == "__main__":
    main()