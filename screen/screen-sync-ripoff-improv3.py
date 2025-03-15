import mss
import numpy as np
import cv2
from PIL import Image, ImageEnhance
import time
import serial
import serial.tools.list_ports
import json
import os
from scipy.spatial import distance

# Configuration File
CONFIG_FILE = "settings.json"

# Grid & Color Processing
GRID_ROWS = 10  # Number of rows in the grid
GRID_COLS = 10  # Number of columns in the grid
UPDATE_INTERVAL = 0.1  # Time in seconds between updates (100ms)
NUM_DISTINCT_COLORS = 6  # Number of colors to send to the ESP32

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
        return SERIAL_PORT

    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports detected.")
        return None

    print("\nAvailable Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    choice = int(input("\nSelect a port number: ")) - 1
    if 0 <= choice < len(ports):
        SERIAL_PORT = ports[choice].device
        config["serial_port"] = SERIAL_PORT
        save_config(config)
        return SERIAL_PORT
    else:
        print("Invalid selection.")

# Auto-Detect & Select Display
def find_monitor():
    """Lists available displays and prompts user to select one."""
    global MONITOR_INDEX
    with mss.mss() as sct:
        if MONITOR_INDEX:
            return MONITOR_INDEX

        print("\nAvailable Monitors:")
        for i, monitor in enumerate(sct.monitors[1:], start=1):
            print(f"  [{i}] {monitor}")

        choice = int(input("\nSelect a monitor number: ")) 
        if 1 <= choice <= len(sct.monitors[1:]):
            MONITOR_INDEX = choice
            config["monitor_index"] = MONITOR_INDEX
            save_config(config)
            return MONITOR_INDEX

SERIAL_PORT = find_serial_port()
MONITOR_INDEX = find_monitor()

# Attempt Serial Connection
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)
    except serial.SerialException:
        print(f"Failed to connect to {SERIAL_PORT}.")

# **Extract Grid Colors**
def get_screen_grid_colors():
    with mss.mss() as sct:
        screen_size = sct.monitors[MONITOR_INDEX]
        width, height = screen_size["width"], screen_size["height"]

        screenshot = sct.grab(screen_size)
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # **Enhance Contrast Without Biasing Blue**
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.2)  # Mild enhancement to avoid color suppression

        img_array = np.array(img)

        # Convert to **LAB Color Space** for better color detection
        img_lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)

        box_width = width // GRID_COLS
        box_height = height // GRID_ROWS

        grid_colors = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x1, y1 = col * box_width, row * box_height
                x2, y2 = x1 + box_width, y1 + box_height

                section = img_lab[y1:y2, x1:x2]

                # **Use Median Instead of Mean**
                avg_color = np.median(section, axis=(0, 1)).astype(int)

                # Convert back to RGB
                avg_color = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_LAB2RGB)[0][0]

                r, g, b = avg_color[0].item(), avg_color[1].item(), avg_color[2].item()
                grid_colors.append({"R": r, "G": g, "B": b})

        return grid_colors

# **Find the 6 Most Distinct Colors**
def get_most_distinct_colors(colors, num_colors=NUM_DISTINCT_COLORS):
    if len(colors) <= num_colors:
        return colors

    color_array = np.array([[c["R"], c["G"], c["B"]] for c in colors])

    # **Boost Reds & Oranges**
    weights = np.array([1.5, 1.0, 0.7])  # Stronger red/orange preference
    weighted_colors = color_array * weights

    dist_matrix = distance.cdist(weighted_colors, weighted_colors, metric="euclidean")
    distinct_scores = np.sum(dist_matrix, axis=1)

    top_indices = np.argsort(distinct_scores)[-num_colors:]
    return [colors[i] for i in top_indices]

# **Display Colors in a Window**
def show_grid_colors(colors):
    if not colors:
        return

    rows, cols = GRID_ROWS, GRID_COLS
    block_size = 40  
    img_height = rows * block_size
    img_width = cols * block_size

    color_grid = np.zeros((img_height, img_width, 3), dtype=np.uint8)

    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            r, g, b = colors[idx]["R"], colors[idx]["G"], colors[idx]["B"]
            x1, y1 = col * block_size, row * block_size
            x2, y2 = x1 + block_size, y1 + block_size

            color_grid[y1:y2, x1:x2] = (b, g, r)

    cv2.imshow("Detected Grid Colors", color_grid)
    cv2.waitKey(1)

# **Stream Colors**
while True:
    colors = get_screen_grid_colors()
    distinct_colors = get_most_distinct_colors(colors)

    json_data = json.dumps({"LEDColors": distinct_colors})
    if ser:
        ser.write(f"{json_data}\n".encode())

    show_grid_colors(colors)
    time.sleep(UPDATE_INTERVAL)