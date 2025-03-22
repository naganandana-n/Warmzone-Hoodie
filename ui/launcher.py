import subprocess
import sys
import os

# ✅ Determine the directory where `launcher.exe` is running
if getattr(sys, 'frozen', False):  # Running as an EXE
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# ✅ Define the full path to `web.py`
script_path = os.path.join(base_dir, "web.py")

# ✅ Ensure `web.py` exists before running
if not os.path.exists(script_path):
    print(f"❌ ERROR: web.py not found at {script_path}")
    input("Press Enter to exit...")
    sys.exit(1)

# ✅ Open a new terminal and run `web.py`, logging any errors
subprocess.Popen(
    ["cmd", "/k", f"cd /d {base_dir} && python web.py"],
    shell=True
)

print(f"✅ Running web.py from {script_path}")