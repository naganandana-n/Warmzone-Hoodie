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

def open_browser_to_setup():
    import webbrowser
    webbrowser.open("http://localhost:5000/vb-setup")

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