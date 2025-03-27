import subprocess
import os

# Get absolute path to web.py
web_py_path = os.path.abspath("web.py")

# PowerShell command to run the web server silently in the background
powershell_command = f'''
Start-Process powershell -ArgumentList "-NoProfile -WindowStyle Hidden -Command python '{web_py_path}'" -WindowStyle Hidden
'''

# Launch the PowerShell command
subprocess.run(["powershell", "-Command", powershell_command], shell=True)