import mss
import numpy as np
import cv2
from PIL import Image, ImageEnhance
import time
import serial
import serial.tools.list_ports
import json
import os

# Configuration File
CONFIG_FILE = "settings.json"

# Grid Settings
GRID_ROWS = 8  # Normal grid rows
GRID_COLS = 8  # Normal grid cols
CENTER_GRID_ROWS = 16  # More granularity in center
CENTER_GRID_COLS = 16  # More granularity in center
UPDATE_INTERVAL = 0.06  # ~60ms per frame for high-speed detection

# Flash Detection Thresholds
FLASH_BRIGHTNESS_THRESHOLD = 180  # Minimum brightness for a "flash"
FLASH_DETECTION_ZONE = 0.3  # Center area of screen (percentage)

# Load Saved Settings (Monitor & Serial Port)
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
        print(f"Using saved serial port: {SERIAL_PORT}")
        return SERIAL_PORT

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports detected. Check your ESP32 connection.")
        return None

    print("\nAvailable Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    while True:
        try:
            choice = int(input("\nSelect a port number: ")) - 1
            if 0 <= choice < len(ports):
                SERIAL_PORT = ports[choice].device
                config["serial_port"] = SERIAL_PORT
                save_config(config)  # Save selection
                return SERIAL_PORT
            else:
                print("Invalid selection. Choose a valid port number.")
        except ValueError:
            print("Please enter a number.")

# Auto-Detect & Select Display
def find_monitor():
    """Lists available displays and prompts user to select one."""
    global MONITOR_INDEX
    with mss.mss() as sct:
        if MONITOR_INDEX:
            print(f"Using saved monitor: {MONITOR_INDEX}")
            return MONITOR_INDEX

        print("\nAvailable Monitors:")
        for i, monitor in enumerate(sct.monitors[1:], start=1):
            print(f"  [{i}] {monitor}")

        while True:
            try:
                choice = int(input("\nSelect a monitor number: ")) 
                if 1 <= choice <= len(sct.monitors[1:]):
                    MONITOR_INDEX = choice
                    config["monitor_index"] = MONITOR_INDEX
                    save_config(config)  # Save selection
                    return MONITOR_INDEX
                else:
                    print("Invalid selection. Choose a valid monitor number.")
            except ValueError:
                print("Please enter a number.")

# Detect and Store Serial Port & Monitor Selection
SERIAL_PORT = find_serial_port()
MONITOR_INDEX = find_monitor()

# Attempt Serial Connection
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)  # Allow ESP32 to initialize
        print(f"Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f"Failed to connect to {SERIAL_PORT}. Check your ESP32 connection.")

# **Extract Grid Colors and Detect Flash**
def get_screen_grid_colors():
    """Breaks the screen into a grid and extracts colors, focusing on center detection."""
    with mss.mss() as sct:
        screen_size = sct.monitors[MONITOR_INDEX]
        width, height = screen_size["width"], screen_size["height"]

        # Capture full screen
        screenshot = sct.grab(screen_size)
        
        # Convert to RGB Image
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Enhance colors
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(3)  # Boost color saturation

        # Convert to NumPy array for fast processing
        img_array = np.array(img)

        # Calculate grid sizes
        box_width = width // GRID_COLS
        box_height = height // GRID_ROWS

        # Center Zone Grid
        center_x1 = int(width * (0.5 - FLASH_DETECTION_ZONE / 2))
        center_y1 = int(height * (0.5 - FLASH_DETECTION_ZONE / 2))
        center_x2 = int(width * (0.5 + FLASH_DETECTION_ZONE / 2))
        center_y2 = int(height * (0.5 + FLASH_DETECTION_ZONE / 2))

        # Extract colors from each grid section
        grid_colors = []
        flash_detected = False
        flash_color = None

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                # Define the box region
                x1, y1 = col * box_width, row * box_height
                x2, y2 = x1 + box_width, y1 + box_height

                # Crop the section
                section = img_array[y1:y2, x1:x2]

                # Compute the mean color in the section
                avg_color = np.mean(section, axis=(0, 1)).astype(int)

                # Convert BGR to RGB
                r, g, b = avg_color[0].item(), avg_color[1].item(), avg_color[2].item()

                # Store the color
                grid_colors.append({"R": r, "G": g, "B": b})

                # Check for flash detection in center
                if center_x1 < x1 < center_x2 and center_y1 < y1 < center_y2:
                    brightness = (r + g + b) / 3
                    if brightness > FLASH_BRIGHTNESS_THRESHOLD:
                        flash_detected = True
                        flash_color = {"R": r, "G": g, "B": b}

        return grid_colors, flash_detected, flash_color

# **Stream Grid Colors to ESP32**
print("Streaming screen grid colors to ESP32 in JSON format...")
while True:
    colors, flash_detected, flash_color = get_screen_grid_colors()

    # If a flash is detected, send only the flash color
    if flash_detected:
        json_data = json.dumps({"Flash": flash_color})
        print(f"🔥 Shot detected! Flash color: {flash_color}")
    else:
        json_data = json.dumps({"GridColors": [{k: int(v) for k, v in color.items()} for color in colors]})

    # Send data over serial
    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f"Sent to ESP32: {json_data}")

    time.sleep(UPDATE_INTERVAL)  # Adjust refresh rate