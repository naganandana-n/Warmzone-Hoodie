import os
import subprocess
import json
import sys
import ctypes
import time

STATE_PATH = os.path.join(os.path.dirname(__file__), "vb_setup_state.json")
SETUP_SCRIPT = os.path.join(os.path.dirname(__file__), "audio", "setup.ps1")
NIRCMD_PATH = os.path.join(os.path.dirname(__file__), "audio", "nircmd.exe")

def show_popup(message, title="Restart Required"):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1)

def is_vb_cable_installed():
    try:
        output = subprocess.check_output(
            ['powershell', '-Command',
             'Get-WmiObject Win32_SoundDevice | Where-Object { $_.Name -like "*VB-Audio*" }'],
            stderr=subprocess.DEVNULL, text=True)
        return bool(output.strip())
    except:
        return False

def create_default_state():
    return {
        "installed": False,
        "setup_done": False
    }

def load_state():
    if not os.path.exists(STATE_PATH):
        with open(STATE_PATH, "w") as f:
            json.dump(create_default_state(), f, indent=2)
        return create_default_state()

    with open(STATE_PATH, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def run_setup_ps1():
    print("🔧 Running setup.ps1...")
    subprocess.call([
        "powershell", "-ExecutionPolicy", "Bypass",
        "-File", SETUP_SCRIPT
    ])
    time.sleep(2)

def launch_web_server():
    controller_dir = os.path.dirname(__file__)
    python_dir = os.path.join(controller_dir, "python-embed")

    # Auto-detect architecture
    arch_map = {
        "AMD64": "python-3.13.2-embed-amd64",
        "x86": "python-3.13.2-embed-win32",
        "ARM64": "python-3.13.2-embed-arm64"
    }

    arch = os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64")
    py_exe = os.path.join(python_dir, arch_map.get(arch, "python-3.13.2-embed-amd64"), "python.exe")
    web_py = os.path.join(controller_dir, "web.py")

    if not os.path.exists(py_exe) or not os.path.exists(web_py):
        print("❌ Cannot launch web server: python.exe or web.py not found")
        return

    print("🚀 Launching web server...")
    subprocess.Popen([py_exe, web_py], cwd=controller_dir)

def open_browser_to_setup():
    launch_web_server()
    time.sleep(2)  # Give the web server time to start
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000/vb_setup")

def main():
    state = load_state()

    if not is_vb_cable_installed():
        print("❌ VB-Audio Cable not detected. Starting installer...")
        run_setup_ps1()
        show_popup("VB-Cable installed. Please restart your computer.", "Restart Needed")
        state["installed"] = False
        state["setup_done"] = False
        save_state(state)
        sys.exit(1)

    # VB-Cable is installed
    state["installed"] = True
    save_state(state)

    if not state.get("setup_done", False):
        print("⚠️ VB-Cable installed but setup not done. Launching guide...")
        open_browser_to_setup()
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
