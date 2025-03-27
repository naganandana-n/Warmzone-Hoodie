import subprocess
import os

web_py_path = os.path.abspath("web.py")
print(f"Running web.py from: {web_py_path}")

powershell_command = f'''
Start-Process powershell -ArgumentList "-NoProfile -WindowStyle Hidden -Command python '{web_py_path}'" -WindowStyle Hidden
'''

print("Launching PowerShell command...")
subprocess.run(["powershell", "-Command", powershell_command], shell=True)
print("Command executed.")