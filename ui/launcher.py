import subprocess
import os
import sys

venv_python = os.path.abspath(sys.executable)  # This gets path to current venv's python
web_py_path = os.path.abspath("web.py")

powershell_command = f'''
Start-Process powershell -ArgumentList "-NoProfile -Command '{venv_python}' '{web_py_path}'"
'''

print("Launching with venv interpreter:", venv_python)
subprocess.run(["powershell", "-Command", powershell_command], shell=True)