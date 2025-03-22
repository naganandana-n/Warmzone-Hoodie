import os
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser
import time

# ✅ Ensure Flask finds `templates/` when running as an .exe
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")  # ✅ Ensure index.html exists inside `templates/`

@socketio.on("button_clicked")
def handle_button_click():
    print("🚀 [INFO] Button Clicked! Event Received from Web UI")

# ✅ New: Function to delay and force the browser to open
def delayed_browser_open():
    time.sleep(2)  # Allow Flask to start before opening browser
    url = "http://127.0.0.1:5000"
    print(f"🌐 [INFO] Opening browser at {url}")
    webbrowser.open(url)

# ✅ New: Function to run Flask server
def run_server():
    threading.Thread(target=delayed_browser_open, daemon=True).start()
    print("🚀 [INFO] Starting Flask Web Server...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run_server()