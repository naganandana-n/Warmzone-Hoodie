from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")  # ✅ Fix async issue

# Global feature states
features = {
    "audio": True,
    "screen": True,
    "mouse": True,
    "heaters": [False, False, False]  # Heater 1, 2, 3 OFF initially
}

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("toggle_feature")
def toggle_feature(data):
    feature = data["feature"]
    if feature in features:
        features[feature] = not features[feature]
        print(f"🔄 {feature} Toggled: {features[feature]}")
    elif feature.startswith("heater"):
        idx = int(feature[-1]) - 1  # Extract heater number
        features["heaters"][idx] = not features["heaters"][idx]
        print(f"🔥 Heater {idx+1} Toggled: {features['heaters'][idx]}")

# **Open Browser Automatically**
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# **Run Flask Server**
def run_server():
    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_server()