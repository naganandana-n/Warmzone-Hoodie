import tkinter as tk
import json
import os
import ctypes
import sys

# ─── COPY FROM YOUR EXISTING SCRIPT ──────────────────────────────────────

NUM_LEDS = 24
DOT_RADIUS = 5

def get_equidistant_points(p0, p1, n):
    x0, y0 = p0
    x1, y1 = p1
    return [(x0 + (x1 - x0) * (i / (n - 1)), y0 + (y1 - y0) * (i / (n - 1))) for i in range(n)]

class LineSelector(tk.Tk):
    def __init__(self, num_lines=2, leds_per_line=12):
        super().__init__()
        self.attributes("-alpha", 0.3)
        self.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self, cursor="cross", bg="gray11", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.canvas.create_line(w//2, 0, w//2, h, fill="white", dash=(4,2))
        self.canvas.create_line(0, h//2, w, h//2, fill="white", dash=(4,2))

        self.num_lines = num_lines
        self.leds_per_line = leds_per_line
        self.clicks = []
        self.lines = []
        self.temp_line = None
        self.points = []

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_motion)

    def on_click(self, event):
        self.clicks.append((event.x, event.y))
        if len(self.clicks) % 2 == 0:
            p0, p1 = self.clicks[-2], self.clicks[-1]
            self.lines.append((p0, p1))
            self.canvas.create_line(*p0, *p1, fill="cyan", width=2)
            if len(self.lines) == self.num_lines:
                self.draw_dots()
                self.canvas.bind("<Button-1>", lambda e: self.quit())

    def on_motion(self, event):
        if len(self.clicks) % 2 == 1:
            p0 = self.clicks[-1]
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(*p0, event.x, event.y, dash=(4,2), fill="cyan")

    def draw_dots(self):
        for p0, p1 in self.lines:
            pts = get_equidistant_points(p0, p1, self.leds_per_line)
            self.points.extend(pts)
            for x, y in pts:
                self.canvas.create_oval(
                    x - DOT_RADIUS, y - DOT_RADIUS,
                    x + DOT_RADIUS, y + DOT_RADIUS,
                    fill="magenta", outline=""
                )

def main():
    app = LineSelector(num_lines=2, leds_per_line=NUM_LEDS // 2)
    if sys.platform == "win32":
        try:
            # Find the window with class name "TkTopLevel"
            hwnd = ctypes.windll.user32.FindWindowW("TkTopLevel", None)
            if hwnd != 0:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"⚠️ Could not bring selector to front: {e}")

    
    app.mainloop()

    # Round and save points as list of dicts for easy JSON use
    rounded_points = [{"x": round(x), "y": round(y)} for (x, y) in app.points]

    output_path = os.path.join(os.path.dirname(__file__), "led_points.json")
    with open(output_path, "w") as f:
        json.dump(rounded_points, f, indent=2)
    print(f"✅ Saved {len(rounded_points)} LED points to {output_path}")

if __name__ == "__main__":
    main()