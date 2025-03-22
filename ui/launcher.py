import os
import sys

# ✅ Determine the directory where `launcher.py` (or `launcher.exe`) is running
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

# ✅ Run `web.py` safely in the same process
with open(script_path, encoding="utf-8") as f:
    code = compile(f.read(), script_path, 'exec')
    exec(code, globals())

print("✅ web.py has been executed")