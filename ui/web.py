from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import webbrowser

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    """Serve the HTML page"""
    return render_template("index.html")

@socketio.on("button_clicked")
def handle_button_click():
    """Handle button click event from the web UI"""
    print("🚀 Button was clicked! Message received from web UI.")

# **Automatically open the browser when the server starts**
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

# **Function to Start the Flask Server**
def run_server():
    threading.Thread(target=open_browser, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    run_server()