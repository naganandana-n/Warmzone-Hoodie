import mss
import numpy as np
import cv2
from PIL import Image, ImageStat, ImageEnhance
import time
import serial
import serial.tools.list_ports
import json
import os

# Configuration File
CONFIG_FILE = "settings.json"

# Screen Capture Settings
SENSOR_SIZES = {
    "tiny": 0.05,
    "small": 0.075,
    "medium": 0.15,
    "large": 0.33,
    "xlarge": 0.5
}

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

# Load Previous Configuration (If Available)
config = load_config()
SERIAL_PORT = config.get("serial_port")
MONITOR_INDEX = config.get("monitor_index")
SENSOR_SIZE = config.get("sensor_size", "small")  # Default to 'small'

# Auto-Detect & Select Serial Port
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
                print("Invalid selection. Please choose a valid port number.")
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

# Function to calculate bounding box size
def calculate_bounding_box(screen_size, sensor_size="small"):
    """Calculates the bounding box for capturing a small portion of the screen."""
    width, height = screen_size
    center_x, center_y = width // 2, height // 2
    offset = int(min(width, height) * SENSOR_SIZES[sensor_size])

    return (center_x - offset, center_y - offset, center_x + offset, center_y + offset)

# **Extract Enhanced Screen Colors**
def get_screen_color():
    """Captures a small area of the screen, enhances colors, and extracts the dominant color."""
    with mss.mss() as sct:
        screen_size = sct.monitors[MONITOR_INDEX]
        bbox = calculate_bounding_box((screen_size["width"], screen_size["height"]), SENSOR_SIZE)

        # Capture selected area
        screenshot = sct.grab(bbox)
        
        # Convert to RGB Image
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Enhance color vibrancy
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(3)  # Boost color saturation

        # Extract dominant color using median
        image_stats = ImageStat.Stat(img)
        dominant_color = tuple(map(int, image_stats.median[:3]))  # (R, G, B)

        return dominant_color

# **Display Colors in a Window**
def show_color(color):
    """Displays detected color in an OpenCV window."""
    height, width = 100, 300
    color_block = np.zeros((height, width, 3), dtype=np.uint8)
    
    r, g, b = color  # RGB format
    color_block[:, :] = (b, g, r)  # OpenCV uses BGR

    cv2.imshow("Detected Color", color_block)
    cv2.waitKey(1)  # Refresh the window

# **Stream Colors to ESP32**
print("Streaming enhanced screen colors to ESP32 in JSON format...")
while True:
    color = get_screen_color()

    # Convert to JSON format
    json_data = json.dumps({"R": color[0], "G": color[1], "B": color[2]})

    # Send data over serial
    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f"Sent to ESP32: {json_data}")

    # Show the color visually in a window
    show_color(color)

    time.sleep(0.1)  # Faster refresh rate