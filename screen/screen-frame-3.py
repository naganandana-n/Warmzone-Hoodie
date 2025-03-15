import mss
import numpy as np
import cv2
from PIL import Image
import time
import serial
import serial.tools.list_ports
import json
import os

# Configuration File
CONFIG_FILE = "settings.json"

# Define Brightness & White Threshold
WHITE_THRESHOLD = 220  # Ignore colors close to white
BRIGHTNESS_THRESHOLD = 70  # Minimum brightness for LEDs

# Load Saved Settings
def load_config():
    """Loads saved monitor & serial port selection from file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

# Save Settings
def save_config(settings):
    """Saves monitor & serial port selection to a file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(settings, file)

# Load Previous Configuration
config = load_config()
SERIAL_PORT = config.get("serial_port")
MONITOR_INDEX = config.get("monitor_index")

# Auto-Detect Serial Port
def find_serial_port():
    """Lists available serial ports and prompts user to select one."""
    global SERIAL_PORT
    if SERIAL_PORT:
        print(f" Using saved serial port: {SERIAL_PORT}")
        return SERIAL_PORT

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print(" No serial ports detected. Check your ESP32 connection.")
        return None

    print("\n Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    while True:
        try:
            choice = int(input("\n Select a port number: ")) - 1
            if 0 <= choice < len(ports):
                SERIAL_PORT = ports[choice].device
                config["serial_port"] = SERIAL_PORT
                save_config(config)  # Save selection
                return SERIAL_PORT
            else:
                print(" Invalid selection. Please choose a valid port number.")
        except ValueError:
            print(" Please enter a number.")

# Auto-Detect & Select Display
def find_monitor():
    """Lists available displays and prompts user to select one."""
    global MONITOR_INDEX
    with mss.mss() as sct:
        if MONITOR_INDEX:
            print(f" Using saved monitor: {MONITOR_INDEX}")
            return MONITOR_INDEX

        print("\n Available Monitors:")
        for i, monitor in enumerate(sct.monitors[1:], start=1):
            print(f"  [{i}] {monitor}")

        while True:
            try:
                choice = int(input("\n Select a monitor number: ")) 
                if 1 <= choice <= len(sct.monitors[1:]):
                    MONITOR_INDEX = choice
                    config["monitor_index"] = MONITOR_INDEX
                    save_config(config)  # Save selection
                    return MONITOR_INDEX
                else:
                    print(" Invalid selection. Choose a valid monitor number.")
            except ValueError:
                print(" Please enter a number.")

# Detect and Store Serial Port & Monitor Selection
SERIAL_PORT = find_serial_port()
MONITOR_INDEX = find_monitor()

# Attempt Serial Connection
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)  # Allow ESP32 to initialize
        print(f" Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f" Failed to connect to {SERIAL_PORT}. Check your ESP32 connection.")

# Store previous frame colors
previous_frame_colors = set()

# **Detect New Bright Colors**
def get_new_colors():
    """Detects all bright new colors appearing in the current frame."""
    global previous_frame_colors

    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[MONITOR_INDEX])
        
        # Convert to RGB Image
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Resize for faster processing
        img = img.resize((100, 100))

        # Convert to NumPy array
        pixels = np.array(img).reshape(-1, 3)

        # **Filter: Remove White & Dark Colors**
        bright_colors = {
            tuple(color) for color in pixels
            if (max(color) >= BRIGHTNESS_THRESHOLD) and not all(c > WHITE_THRESHOLD for c in color)
        }

        # **Find only new colors**
        new_colors = bright_colors - previous_frame_colors
        previous_frame_colors = bright_colors  # Update for next frame

        return list(new_colors)

# **Display Colors in a Window**
def show_colors(colors):
    """Displays detected colors in an OpenCV window."""
    if not colors:
        return

    height = 100
    width = 300
    color_blocks = np.zeros((height, width, 3), dtype=np.uint8)

    # Split the window equally based on the number of colors
    section_width = width // len(colors)

    for i, color in enumerate(colors):
        r, g, b = color  # RGB format
        start_x = i * section_width
        end_x = start_x + section_width
        color_blocks[:, start_x:end_x] = (b, g, r)  # OpenCV uses BGR

    cv2.imshow("New Bright Colors", color_blocks)
    cv2.waitKey(1)  # Refresh the window

# **Stream New Colors to ESP32**
print(" Streaming new bright colors to ESP32 in JSON format...")
while True:
    colors = get_new_colors()
    
    if colors:
        # Convert to JSON format
        json_data = json.dumps({"NewColors": colors})

        # Send data over serial
        if ser:
            ser.write(f"{json_data}\n".encode())
            print(f" Sent to ESP32: {json_data}")

        # Show colors visually in a window
        show_colors(colors)

    time.sleep(0.1)  # **Increased speed (10x faster than before)**