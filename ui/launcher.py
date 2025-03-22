import subprocess
import os
import sys

# Get the absolute path to web.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_SCRIPT = os.path.join(BASE_DIR, "web.py")

# Use the correct Python executable
PYTHON_EXECUTABLE = sys.executable

# Run web.py (and keep the terminal open)
subprocess.run([PYTHON_EXECUTABLE, WEB_SCRIPT])