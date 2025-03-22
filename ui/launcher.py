import subprocess
import os
import sys

# Locate the web.py script
web_script = os.path.join(os.path.dirname(__file__), "web.py")

if not os.path.exists(web_script):
    print(f"❌ ERROR: web.py not found at {web_script}")
    sys.exit(1)

try:
    print(f"🚀 Launching web.py from {web_script}...")
    
    # Run web.py with the default Python interpreter
    subprocess.Popen(["python", web_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print("✅ Web server should be running!")
except Exception as e:
    print(f"❌ ERROR: {e}")