import subprocess
import sys
import os

# ✅ Get the current directory where `launcher.exe` is running
if getattr(sys, 'frozen', False):  # Running as an EXE
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(__file__)

# ✅ Path to `web.py` in the same folder as `launcher.exe`
script_path = os.path.join(base_dir, "web.py")

# ✅ Check if `web.py` exists
if not os.path.exists(script_path):
    print(f"❌ ERROR: web.py not found at {script_path}")
    input("Press Enter to exit...")
    sys.exit(1)

# ✅ Open a new terminal and run `web.py` in the same directory
subprocess.Popen(
    ["cmd.exe", "/K", f"cd /d {base_dir} && python web.py"],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)