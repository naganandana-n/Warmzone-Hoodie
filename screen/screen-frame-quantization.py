import mss
import numpy as np
import cv2
from PIL import Image
import time
import serial
import serial.tools.list_ports
import json
import os
from collections import Counter

# Configuration File
CONFIG_FILE = "settings.json"

# White threshold: Any color with all RGB values above this will be ignored
WHITE_THRESHOLD = 220  

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
                print(" Invalid selection. Choose a valid port number.")
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
previous_frame_colors = None

# **Extract Dominant Colors Using Histogram**
def get_dominant_colors(num_colors=5):
    """Extracts the most frequent colors from the screen using histograms instead of K-Means."""
    global previous_frame_colors

    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[MONITOR_INDEX])
        
        # Convert to RGB Image
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Resize for faster processing
        img = img.resize((100, 100))

        # Convert to NumPy array
        pixels = np.array(img).reshape(-1, 3)

        # Convert to tuples for histogram counting
        color_counts = Counter(map(tuple, pixels))

        # Sort colors by frequency
        sorted_colors = [color for color, _ in color_counts.most_common(num_colors)]

        # Filter out colors that are too close to white
        filtered_colors = [
            color for color in sorted_colors if not all(c > WHITE_THRESHOLD for c in color)
        ]

        if previous_frame_colors is None:
            previous_frame_colors = set(filtered_colors)
            return filtered_colors[:2]

        # Find only changed colors
        changed_colors = [color for color in filtered_colors if color not in previous_frame_colors]

        # Update stored colors
        previous_frame_colors = set(filtered_colors)

        return changed_colors[:2]  # Return top 2 changed colors

# **Display Changed Colors in a Window**
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

    cv2.imshow("Changed Colors", color_blocks)
    cv2.waitKey(1)  # Refresh the window

# **Stream Changed Colors to ESP32**
print(" Streaming dominant screen colors to ESP32 in JSON format...")
while True:
    colors = get_dominant_colors()
    
    if colors:
        # Convert to JSON format
        json_data = json.dumps({"Color1": colors[0], "Color2": colors[1]})

        # Send data over serial
        if ser:
            ser.write(f"{json_data}\n".encode())
            print(f" Sent to ESP32: {json_data}")

        # Show colors visually in a window
        show_colors(colors)

    time.sleep(0.5)  # Adjust refresh rate as needed