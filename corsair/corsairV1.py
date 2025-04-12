import tkinter as tk
import mss
from PIL import Image
import numpy as np
import time
import serial

# ─── CONFIG ────────────────────────────────────────────────────────────────
SERIAL_PORT = "COM5"      # e.g. "COM3" on Windows or "/dev/ttyUSB0" on Linux/macOS
BAUD_RATE   = 115200
NUM_LEDS    = 24
SAMPLE_FPS  = 20          # how many times per second to sample/send
DOT_RADIUS  = 5           # radius in pixels for the overlay dots
# ──────────────────────────────────────────────────────────────────────────

# ─── GUI FOR LINE SELECTION & DOT OVERLAY ─────────────────────────────────

class LineSelector(tk.Tk):
    def __init__(self, num_lines=2, leds_per_line=12):
        super().__init__()
        self.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray11", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.num_lines = num_lines
        self.leds_per_line = leds_per_line
        self.clicks = []        # raw click positions
        self.lines = []         # finalized lines
        self.temp_line = None

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)

    def on_click(self, event):
        self.clicks.append((event.x, event.y))
        # every two clicks finalize one line
        if len(self.clicks) % 2 == 0:
            p0 = self.clicks[-2]
            p1 = self.clicks[-1]
            self.lines.append((p0, p1))
            # draw the permanent line
            self.canvas.create_line(*p0, *p1, fill="cyan", width=2)
            if len(self.lines) == self.num_lines:
                # once both lines defined, draw the dots
                self.draw_dots()
                # leave the GUI open so user can confirm; close on click
                self.canvas.bind("<Button-1>", lambda e: self.destroy())

    def on_motion(self, event):
        # draw a dashed preview of the current line
        if len(self.clicks) % 2 == 1:
            p0 = self.clicks[-1]
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(*p0, event.x, event.y,
                                                     dash=(4,2), fill="cyan")

    def draw_dots(self):
        # for each line, compute equally spaced points and draw a small circle
        for p0, p1 in self.lines:
            points = get_equidistant_points(p0, p1, self.leds_per_line)
            for x, y in points:
                self.canvas.create_oval(
                    x - DOT_RADIUS, y - DOT_RADIUS,
                    x + DOT_RADIUS, y + DOT_RADIUS,
                    fill="magenta", outline=""
                )

def select_two_lines():
    """
    Launch fullscreen, let user click 4 times:
      click1 → start of line1
      click2 → end   of line1
      click3 → start of line2
      click4 → end   of line2
    Then shows the 24 sample‐point dots; final click closes.
    Returns: [((x0,y0),(x1,y1)), ((x0,y0),(x1,y1))]
    """
    app = LineSelector(num_lines=2, leds_per_line=NUM_LEDS // 2)
    app.mainloop()
    return app.lines

# ─── SAMPLE‐POINT CALCULATION ─────────────────────────────────────────────

def get_equidistant_points(p0, p1, n):
    x0,y0 = p0; x1,y1 = p1
    return [ (x0 + (x1-x0)*(i/(n-1)), y0 + (y1-y0)*(i/(n-1))) for i in range(n) ]

# ─── SCREEN COLOR EXTRACTION ────────────────────────────────────────────

'''
# single point extraction

def sample_colors_at(points):
    colors = []
    with mss.mss() as sct:
        for x,y in points:
            region = {"left": int(x), "top": int(y), "width": 1, "height": 1}
            img = sct.grab(region)
            r,g,b = img.pixel(0,0)
            colors.append((r,g,b))
    return colors
'''
# ─── SCREEN COLOR EXTRACTION WITH 3×3 AVERAGING ──────────────────────────

def sample_colors_at(points, window=3):
    """
    For each (x,y) in points, grab a window×window block centered on it,
    average all pixels in that block, and return a list of averaged (R,G,B) tuples.
    """
    half = window // 2
    colors = []
    with mss.mss() as sct:
        for x, y in points:
            # define the capture region
            left = int(x) - half
            top  = int(y) - half
            region = {
                "left": left,
                "top": top,
                "width": window,
                "height": window
            }
            img = sct.grab(region)
            # convert raw bytes to a (window × window × 3) array
            arr = np.frombuffer(img.rgb, dtype=np.uint8)
            arr = arr.reshape((window, window, 3))
            # average over the first two axes (height, width)
            avg = tuple(arr.mean(axis=(0, 1)).astype(int))
            colors.append(avg)
    return colors
# ─── SERIAL LED OUTPUT ───────────────────────────────────────────────────

class SerialLEDController:
    def __init__(self, port, baud, num_leds):
        self.num_leds = num_leds
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # allow ESP32 to reset
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

    def send_colors(self, colors):
        if len(colors) != self.num_leds:
            raise ValueError(f"Expected {self.num_leds} colors, got {len(colors)}")

        # DEBUG: print out what we're sending
        black_count = sum(1 for c in colors if c == (0, 0, 0))
        print(f"Sending frame: first 3 LEDs {colors[:3]}, last 3 LEDs {colors[-3:]}, black count = {black_count}/{self.num_leds}")

        data = bytearray()
        for (r, g, b) in colors:
            data += bytes((r, g, b))
        self.ser.write(data)
        self.ser.flush()

    def close(self):
        self.ser.close()

# ─── MAIN LOOP ──────────────────────────────────────────────────────────

def main():
    print("Click to define two lines (4 clicks total)...")
    lines = select_two_lines()

    points = []
    for p0, p1 in lines:
        pts = get_equidistant_points(p0, p1, NUM_LEDS // 2)
        points.extend(pts)

    print(f"Sampling {len(points)} points @ {SAMPLE_FPS} FPS. Opening serial on {SERIAL_PORT}@{BAUD_RATE}...")
    controller = SerialLEDController(SERIAL_PORT, BAUD_RATE, NUM_LEDS)

    interval = 1.0 / SAMPLE_FPS
    try:
        while True:
            start = time.time()
            cols = sample_colors_at(points)
            controller.send_colors(cols)
            elapsed = time.time() - start
            if elapsed < interval:
                time.sleep(interval - elapsed)
    except KeyboardInterrupt:
        print("Exiting.")
    finally:
        controller.close()

if __name__ == "__main__":
    main()