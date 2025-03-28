from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser
import os
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Feature States
state = {
    "audio": True,
    "screen": True,
    "mouse": True,
    "sensitivity": 3,
    "heaters": [1, 1, 1],
    "vibration": False,
    "sync_with_audio": False
}

CONTROL_JSON_PATH = os.path.join(os.path.dirname(__file__), "control_state.json")

def write_state_to_json():
    try:
        with open(CONTROL_JSON_PATH, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to write to JSON: {e}")

@app.route("/")
def index():
    return render_template("index.html", state=state)

@socketio.on("toggle")
def toggle(data):
    key = data["key"]
    if key in state:
        state[key] = not state[key]
    elif key.startswith("heater"):
        idx = int(key[-1]) - 1
        state["heaters"][idx] = data["value"]
    elif key == "sensitivity":
        state["sensitivity"] = data["value"]

    print(f"🔄 Updated state: {state}")
    write_state_to_json()

@socketio.on("shutdown")
def shutdown():
    print("🛑 Shutdown requested from client.")
    os._exit(0)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

def run_server():
    # Write initial state on startup
    write_state_to_json()
    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_server()