from flask import Flask, render_template
import threading
import webbrowser
import time

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

def open_browser():
    """ Open the browser after a small delay to allow the server to start """
    time.sleep(1)  # Small delay to ensure the server is running
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()  # Open browser automatically
    app.run(host="0.0.0.0", port=5000, debug=False)
    
    # Prevents terminal from closing
    input("\nPress Enter to exit...\n")