import subprocess
import sys

# **Run `web.py` using Python**
try:
    print("🚀 [INFO] Launching Web Server...")
    subprocess.Popen([sys.executable, "web.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
except Exception as e:
    print(f"❌ [ERROR] Failed to launch web.py: {e}")