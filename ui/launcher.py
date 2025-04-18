import os
import sys
import subprocess

# Correctly get base path whether running as .py or as .exe
if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))

# Get absolute path to web.py
web_py_path = os.path.join(current_dir, "web.py")

# Get Python executable from current environment (e.g., venv)
python_executable = sys.executable

print(f"Launching web.py using Python: {python_executable}")
print(f"web.py path: {web_py_path}")

# Launch web.py using subprocess
subprocess.Popen(
    [python_executable, web_py_path],
    cwd=current_dir,
    creationflags=subprocess.CREATE_NO_WINDOW  # Hide terminal window (on .exe build)
)