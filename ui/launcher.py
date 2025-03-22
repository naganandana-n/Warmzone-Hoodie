import subprocess
import sys
import os

# ✅ Get the current directory where the EXE is running
if getattr(sys, 'frozen', False):  # When running as an EXE
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

# ✅ Get the Python interpreter being used
python_executable = sys.executable  

# ✅ Launch `web.py` in a new terminal
subprocess.Popen([python_executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)