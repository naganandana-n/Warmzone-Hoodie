import tkinter as tk
import mss
from PIL import Image
import numpy as np
import time
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

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
        # when two clicks collected → store a line
        if len(self.clicks) % 2 == 0:
            p0 = self.clicks[-2]
            p1 = self.clicks[-1]
            self.lines.append((p0, p1))
            # draw permanent line
            self.canvas.create_line(*p0, *p1, fill="cyan", width=2)
            if len(self.lines) == self.num_lines:
                self.destroy()

    def on_motion(self, event):
        # draw temporary line from last click to cursor
        if len(self.clicks) % 2 == 1:
            p0 = self.clicks[-1]
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(*p0, event.x, event.y, dash=(4,2), fill="cyan")

def select_two_lines():
    """
    Launches fullscreen, lets user click four times:
      click1 → start of line1
      click2 → end   of line1
      click3 → start of line2
      click4 → end   of line2
    Returns: [((x0,y0),(x1,y1)), ((x0,y0),(x1,y1))]
    """
    app = LineSelector(num_lines=2)
    app.mainloop()
    return app.lines


# ─── SAMPLE‐POINT CALCULATION ─────────────────────────────────────────────

def get_equidistant_points(p0, p1, n):
    """
    p0, p1: (x,y) endpoints
    n: number of points
    returns list of (x,y) floats
    """
    x0,y0 = p0; x1,y1 = p1
    return [ (x0 + (x1-x0)*(i/(n-1)), y0 + (y1-y0)*(i/(n-1))) for i in range(n) ]


# ─── SCREEN COLOR EXTRACTION ────────────────────────────────────────────

def sample_colors_at(points):
    """
    points: list of (x,y) floats
    returns: list of (R,G,B) ints
    """
    colors = []
    with mss.mss() as sct:
        for x,y in points:
            # grab 1×1 pixel around the point
            region = {"left": int(x), "top": int(y), "width": 1, "height": 1}
            img = sct.grab(region)
            # img.rgb is raw bytes in R,G,B order
            r,g,b = img.pixel(0,0)
            colors.append((r,g,b))
    return colors


# ─── LED OUTPUT (OpenRGB) ───────────────────────────────────────────────

class LEDController:
    def __init__(self):
        self.client = OpenRGBClient()    # make sure OpenRGB daemon is running
        self.devices = self.client.devices

    def set_all(self, colors):
        """
        colors: list of (R,G,B) tuples, length must match total LEDs (24)
        """
        # you could map subsets of colors to different devices or zones here
        # for simplicity we set every LED on every device to the average:
        for dev in self.devices:
            # OpenRGB API: set entire device to one color, so we average
            avg = np.mean(colors, axis=0).astype(int)
            dev.set_color(RGBColor(*avg))


# ─── MAIN LOOP ──────────────────────────────────────────────────────────

def main():
    print("Click to define two lines (4 clicks total)...")
    lines = select_two_lines()
    # build our 24 sample points
    points = []
    for p0,p1 in lines:
        pts = get_equidistant_points(p0,p1,12)
        points.extend(pts)

    print("Sampling", len(points), "points. Starting LED controller...")
    controller = LEDController()

    try:
        while True:
            cols = sample_colors_at(points)
            controller.set_all(cols)
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()