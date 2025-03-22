from flask import Flask, render_template
from flask_socketio import SocketIO
import webbrowser
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("index.html")  # Ensure index.html is in 'templates' folder

@socketio.on("button_clicked")
def handle_button_click():
    print("🚀 [INFO] Button Clicked! Event Received from Web UI")

# **Automatically open the browser after the server starts**
def delayed_browser_open():
    time.sleep(1)  # Ensure the server starts first
    webbrowser.open("http://127.0.0.1:5000")

# **Run Flask Server**
def run_server():
    threading.Thread(target=delayed_browser_open, daemon=True).start()
    print("🚀 [INFO] Starting Flask Web Server...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

if __name__ == "__main__":
    run_server()