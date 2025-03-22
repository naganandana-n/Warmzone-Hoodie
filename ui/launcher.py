import subprocess
import os
import sys

# ✅ Ensure correct path to `web.py`
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_SCRIPT = os.path.join(BASE_DIR, "web.py")

# ✅ Ensure Python executable is detected
PYTHON_EXECUTABLE = sys.executable if hasattr(sys, "executable") else "python"

# ✅ Start `web.py` in a new process
print(f"🚀 [INFO] Launching web.py using {PYTHON_EXECUTABLE}")
subprocess.Popen([PYTHON_EXECUTABLE, WEB_SCRIPT], creationflags=subprocess.CREATE_NEW_CONSOLE)