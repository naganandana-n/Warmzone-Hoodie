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

# Minimum brightness for LED visibility (0-255 scale)
MIN_BRIGHTNESS_THRESHOLD = 50  
CONTRAST_WEIGHT = 1.5  # Higher means more contrast influence

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

# Auto-Detect Monitor
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

# **🔍 Contrast Calculation**
def color_luminance(color):
    """Calculates luminance based on human perception."""
    r, g, b = color
    return 0.299 * r + 0.587 * g + 0.114 * b  # Standard luminance formula

def color_contrast(c1, c2):
    """Calculates contrast difference between two colors."""
    return abs(color_luminance(c1) - color_luminance(c2))

# **🔄 Screen Color Extraction**
def get_top_screen_colors(num_colors=5, min_color_percentage=20):
    """Captures the screen and extracts the top 2 most visually distinct colors."""
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[MONITOR_INDEX])
        
        # Convert to RGB Image
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Resize for faster processing
        img = img.resize((100, 100))

        # Convert to NumPy array and reshape
        pixels = np.array(img).reshape(-1, 3)

        # Use K-Means to find dominant colors
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)

        # Count occurrences
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        total_pixels = len(pixels)

        # Extract colors that occupy more than min threshold
        filtered_colors = []
        for label, count in zip(labels, counts):
            percentage = (count / total_pixels) * 100
            color = tuple(map(int, kmeans.cluster_centers_[label]))

            # Ensure color is bright enough & meets min percentage threshold
            if (max(color) >= MIN_BRIGHTNESS_THRESHOLD) and (percentage >= min_color_percentage):
                filtered_colors.append({
                    "RGB": (color[2], color[1], color[0]),  # Convert BGR → RGB
                    "Percentage": round(percentage, 2)
                })

        # **Step 1: Sort by highest contrast difference**
        sorted_colors = sorted(
            filtered_colors,
            key=lambda x: color_contrast(x["RGB"], (128, 128, 128)) * CONTRAST_WEIGHT + x["Percentage"],
            reverse=True
        )

        # **Step 2: Return top 2 colors**
        return sorted_colors[:2]

# 🔄 **Stream Top 2 Colors to ESP32**
print(" Streaming top 2 contrast colors to ESP32 in JSON format...")
while True:
    colors = get_top_screen_colors()
    
    # Convert to JSON format
    json_data = json.dumps(colors)

    # Send data over serial
    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f" Sent to ESP32: {json_data}")

    time.sleep(0.5)  # Adjust refresh rate as needed