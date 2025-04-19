from flask import Flask, render_template, request, jsonify, redirect
from flask_socketio import SocketIO
import threading
import webbrowser
import os
import json
import serial.tools.list_ports
import subprocess
import tkinter as tk
import mss
import numpy as np

NUM_LEDS = 24
DOT_RADIUS = 5

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
                self.canvas.bind("<Button-1>", lambda e: self.destroy())

    def on_motion(self, event):
        if len(self.clicks) % 2 == 1:
            p0 = self.clicks[-1]
            if self.temp_line:
                self.canvas.delete(self.temp_line)
            self.temp_line = self.canvas.create_line(*p0, event.x, event.y, dash=(4,2), fill="cyan")

    def draw_dots(self):
        for p0, p1 in self.lines:
            pts = get_equidistant_points(p0, p1, self.leds_per_line)
            for x, y in pts:
                self.canvas.create_oval(
                    x - DOT_RADIUS, y - DOT_RADIUS,
                    x + DOT_RADIUS, y + DOT_RADIUS,
                    fill="magenta", outline=""
                )

def select_two_lines():
    app = LineSelector(num_lines=2, leds_per_line=NUM_LEDS // 2)
    app.mainloop()
    return app.lines

def get_equidistant_points(p0, p1, n):
    x0,y0 = p0
    x1,y1 = p1
    return [(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * i / (n - 1)) for i in range(n)]

def sample_colors_at(points, window=3):
    half = window // 2
    colors = []
    with mss.mss() as sct:
        for x, y in points:
            left = int(x) - half
            top = int(y) - half
            region = {
                "left": left,
                "top": top,
                "width": window,
                "height": window
            }
            img = sct.grab(region)
            arr = np.frombuffer(img.rgb, dtype=np.uint8)
            arr = arr.reshape((window, window, 3))
            avg = tuple(arr.mean(axis=(0, 1)).astype(int))
            colors.append(avg)
    return colors

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Load saved state or use default
CONTROL_JSON_PATH = os.path.join(os.path.dirname(__file__), "control_state.json")
VB_SETUP_STATE_PATH = os.path.join(os.path.dirname(__file__), "vb_setup_state.json")
SHUTDOWN_FLAG_PATH = os.path.join(os.path.dirname(__file__), "shutdown_flag.json")
SELECTED_PORT_PATH = os.path.join(os.path.dirname(__file__), "selected_port.json")


def load_state_from_json():
    try:
        with open(CONTROL_JSON_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load previous state. Using default: {e}")
        return {
            "audio": True,
            "screen": True,
            "mouse": True,
            "sensitivity": 3,
            "heaters": [1, 1, 1],
            "vibration": False,
            "sync_with_audio": False,
            "lights_enabled": True
        }

state = load_state_from_json()


def write_state_to_json():
    try:
        with open(CONTROL_JSON_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to write to JSON: {e}")


@app.route("/")
def index():
    # Check VB setup state first
    if os.path.exists(VB_SETUP_STATE_PATH):
        with open(VB_SETUP_STATE_PATH, "r") as f:
            vb_state = json.load(f)
            if not vb_state.get("installed", False):
                return "VB-Cable not installed. Please restart the app after install."
            elif not vb_state.get("setup_done", False):
                return redirect("/vb_setup")
    return render_template("index.html", state=state)


@app.route("/vb_setup")
def vb_setup():
    return render_template("vb_setup.html")


@app.route("/vb_setup_done", methods=["POST"])
def vb_setup_done():
    try:
        with open(VB_SETUP_STATE_PATH, "r") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data["setup_done"] = True
    with open(VB_SETUP_STATE_PATH, "w") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status": "ok"})


@app.route("/open_sound_settings")
def open_sound_settings():
    try:
        subprocess.Popen([
            "powershell", "-WindowStyle", "Hidden",
            "Start-Process", "mmsys.cpl", "-ArgumentList", "recording"
        ], shell=True)
        print("🔊 Opened Sound Settings via PowerShell.")
        return jsonify({"status": "launched"})
    except Exception as e:
        print(f"❌ Failed to open sound settings: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@socketio.on("toggle")
def toggle(data):
    key = data["key"]

    if key == "sensitivity":
        state["sensitivity"] = data["value"]
    elif key.startswith("heater"):
        idx = int(key[-1]) - 1
        state["heaters"][idx] = data["value"]
    elif key in state and isinstance(state[key], bool):
        state[key] = not state[key]
    elif key == "lights_enabled":
        state["lights_enabled"] = not state.get("lights_enabled", True) 

    print(f"🔄 Updated state: {state}")
    write_state_to_json()

@socketio.on("screen_selection_requested")
def screen_selection_requested():
    import time
    
    SCREEN_POINTS_PATH = os.path.join(os.path.dirname(__file__), "screen_points.json")
    NUM_LEDS = 24  # Update if your LED count changes

    try:
        print("🖱️ Screen selection confirmed. Preparing in 5 seconds...")
        time.sleep(5)  # Let the user prepare their screen
        lines = select_two_lines()

        if not lines:
            print("⚠️ No lines were selected.")
            return

        points = []
        for p0, p1 in lines:
            points.extend(get_equidistant_points(p0, p1, NUM_LEDS // 2))

        with open(SCREEN_POINTS_PATH, "w") as f:
            json.dump(points, f)

        print(f"✅ Screen points saved to {SCREEN_POINTS_PATH} with {len(points)} points.")
        socketio.emit("screen_selection_complete", {"points": len(points)})

    except Exception as e:
        print(f"❌ Error during screen line selection: {e}")
        socketio.emit("screen_selection_complete", {"points": 0})


def write_shutdown_flag():
    try:
        with open(SHUTDOWN_FLAG_PATH, "w") as f:
            json.dump({"shutdown": True}, f)
    except Exception as e:
        print(f"❌ Failed to write shutdown flag: {e}")


@socketio.on("shutdown")
def shutdown():
    print("🛑 Shutdown requested from client.")
    write_shutdown_flag()
    os._exit(0)


def get_serial_ports():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        print(f"🔌 Detected port: {p.device} - {p.description}")
    return [
        {"device": p.device, "description": p.description}
        for p in ports
        if any(x in p.description.lower() for x in ["ch340"])
    ]


@app.route("/ports")
def ports():
    ports = get_serial_ports()
    selected_port = None

    if os.path.exists(SELECTED_PORT_PATH):
        try:
            with open(SELECTED_PORT_PATH, "r") as f:
                selected_data = json.load(f)
                selected_port = selected_data.get("port")
        except Exception as e:
            print(f"⚠️ Failed to read selected_port.json: {e}")

    response = {
        "ports": ports,
        "auto_connected": False,
        "selected_port": selected_port
    }

    if len(ports) == 1:
        try:
            with open(SELECTED_PORT_PATH, "w") as f:
                json.dump({"port": ports[0]["device"]}, f)
            print(f"✅ Auto-saved port: {ports[0]['device']}")
            response["auto_connected"] = True
        except Exception as e:
            print(f"❌ Failed to auto-save port: {e}")
            response["auto_connected"] = False

    return jsonify(response)


@app.route("/save_port", methods=["POST"])
def save_port():
    try:
        data = request.get_json()
        port = data.get("port")
        if port:
            with open(SELECTED_PORT_PATH, "w") as f:
                json.dump({"port": port}, f)
            print(f"💾 Saved selected port: {port}")
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "No port provided"}), 400
    except Exception as e:
        print(f"❌ Failed to save port: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


def run_server():
    write_state_to_json()

    # Only open browser if VB-Cable setup is complete
    skip_browser = False
    if os.path.exists(VB_SETUP_STATE_PATH):
        try:
            with open(VB_SETUP_STATE_PATH, "r") as f:
                vb_state = json.load(f)
                if not vb_state.get("setup_done", False):
                    skip_browser = True
        except:
            skip_browser = True

    if not skip_browser:
        threading.Thread(target=open_browser, daemon=True).start()

    socketio.run(app, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    run_server()