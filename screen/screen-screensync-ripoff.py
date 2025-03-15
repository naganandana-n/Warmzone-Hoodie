import numpy as np
import cv2
import serial
import serial.tools.list_ports
import json
import os
import time
from PIL import ImageGrab, Image

# Configuration File
CONFIG_FILE = "settings.json"

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

# Detect and Store Serial Port Selection
SERIAL_PORT = find_serial_port()

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
previous_frame = None

# **Extract Changed Colors**
def get_changed_colors():
    """Captures the screen, compares to previous frame, and returns new colors."""
    global previous_frame

    # Take a screenshot of the full screen
    screenshot = ImageGrab.grab()

    # Resize for faster processing
    img = screenshot.resize((100, 100))

    # Convert to NumPy array
    pixels = np.array(img)

    if previous_frame is None:
        previous_frame = pixels
        return []  # No changes in the first frame

    # Calculate difference between frames
    diff = np.abs(pixels.astype(int) - previous_frame.astype(int))

    # Update the previous frame
    previous_frame = pixels

    # Extract changed pixels (non-zero values)
    changed_pixels = pixels[np.any(diff > 0, axis=-1)]

    # Get unique colors from changed pixels
    unique_colors = [tuple(map(int, color)) for color in np.unique(changed_pixels, axis=0)]

    return unique_colors

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

    cv2.imshow("Changed Colors", color_blocks)
    cv2.waitKey(1)  # Refresh the window

# **Stream Changed Colors to ESP32**
print(" Streaming changed screen colors to ESP32 in JSON format...")
while True:
    colors = get_changed_colors()
    
    if colors:
        # Convert to JSON format
        json_data = json.dumps({"ChangedColors": colors})

        # Send data over serial
        if ser:
            ser.write(f"{json_data}\n".encode())
            print(f" Sent to ESP32: {json_data}")

        # Show colors visually in a window
        show_colors(colors)

    time.sleep(0.05)  # **Fast updates (20 FPS)**