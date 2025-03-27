import subprocess
import sys
import os

# Get absolute path to web.py
current_dir = os.path.dirname(os.path.abspath(__file__))
web_py_path = os.path.join(current_dir, "web.py")

# Get the Python interpreter from the current environment (likely venv)
python_executable = sys.executable

# Set startup info to suppress window
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# Launch web.py silently
subprocess.Popen(
    [python_executable, web_py_path],
    cwd=current_dir,
    startupinfo=startupinfo,
    creationflags=subprocess.CREATE_NO_WINDOW
)