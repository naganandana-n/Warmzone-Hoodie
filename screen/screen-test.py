import mss
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import time
import serial
import serial.tools.list_ports
import json
import os

# Configuration File
CONFIG_FILE = "settings.json"

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

# Auto-Detect & Select Serial Port
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
        for i, monitor in enumerate(sct.monitors[1:], start=1):  # Ignore monitor[0] (virtual full-screen)
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

# Capture & Process Screen Colors
def get_top_colors_per_quadrant(num_colors=1):
    """Captures the selected screen, extracts dominant color from 4 quadrants, and sends to ESP32."""
    with mss.mss() as sct:
        # Capture the selected monitor
        screenshot = sct.grab(sct.monitors[MONITOR_INDEX]) 
        
        # Convert to PIL Image (Ensure RGB Mode)
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Get screen dimensions
        width, height = img.size

        # Define quadrants (split along x and y)
        quadrants = {
            "TL": img.crop((0, 0, width//2, height//2)),        # Top-Left
            "TR": img.crop((width//2, 0, width, height//2)),    # Top-Right
            "BL": img.crop((0, height//2, width//2, height)),   # Bottom-Left
            "BR": img.crop((width//2, height//2, width, height)) # Bottom-Right
        }

        dominant_colors = {}

        for quadrant, image in quadrants.items():
            # Resize for faster processing
            image = image.resize((50, 50))

            # Convert to NumPy array and reshape
            pixels = np.array(image).reshape(-1, 3)  

            # Use K-Means to find the dominant color
            kmeans = KMeans(n_clusters=num_colors, n_init=10)
            kmeans.fit(pixels)

            # Get the dominant color (ensuring RGB format)
            color = tuple(kmeans.cluster_centers_[0].astype(int))
            dominant_colors[quadrant] = {"R": color[0], "G": color[1], "B": color[2]}

        return dominant_colors

# 🔄 Stream Quadrant Colors to ESP32
print(" Streaming quadrant colors to ESP32 in JSON format...")
while True:
    colors = get_top_colors_per_quadrant()
    
    # Convert to JSON format
    json_data = json.dumps(colors)

    # Send data over serial
    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f" Sent to ESP32: {json_data}")

    time.sleep(0.5)  # Adjust refresh rate as needed