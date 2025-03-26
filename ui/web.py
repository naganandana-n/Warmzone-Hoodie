from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser

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

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

def run_server():
    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_server()