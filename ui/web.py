from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser
import os
import json
import serial.tools.list_ports
from flask import jsonify
from flask import request

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
SHUTDOWN_FLAG_PATH = os.path.join(os.path.dirname(__file__), "shutdown_flag.json")
SELECTED_PORT_PATH = os.path.join(os.path.dirname(__file__), "selected_port.json")

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

    if key == "sensitivity":
        state["sensitivity"] = data["value"]
    elif key.startswith("heater"):
        idx = int(key[-1]) - 1
        state["heaters"][idx] = data["value"]
    elif key in state and isinstance(state[key], bool):
        state[key] = not state[key]

    print(f"🔄 Updated state: {state}")
    write_state_to_json()

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
    return [
        {"device": p.device, "description": p.description}
        for p in ports if "serial" in p.description.lower()
    ]

@app.route("/ports")
def ports():
    ports = get_serial_ports()
    response = {"ports": ports, "auto_connected": False}

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
    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_server()