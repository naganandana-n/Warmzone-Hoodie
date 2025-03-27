import subprocess
import os
import sys

# Determine the correct path to web.py (whether running as .py or .exe)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

web_py_path = os.path.join(base_path, "web.py")

# PowerShell command to run web.py in background
powershell_command = f'''
Start-Process powershell -ArgumentList "-NoProfile -WindowStyle Hidden -Command python '{web_py_path}'" -WindowStyle Hidden
'''

# Execute PowerShell command
subprocess.run(["powershell", "-Command", powershell_command], shell=True)