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
GRID_ROWS = 10  
GRID_COLS = 10  
UPDATE_INTERVAL = 0.1  
NUM_DISTINCT_COLORS = 6  
BRIGHTNESS_THRESHOLD = 60  # Ignore colors that are too dark (0-255 scale)
COLOR_SIMILARITY_THRESHOLD = 80  # Avoid selecting visually similar colors

# Load Settings
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

def save_config(settings):
    with open(CONFIG_FILE, "w") as file:
        json.dump(settings, file)

config = load_config()
SERIAL_PORT = config.get("serial_port")
MONITOR_INDEX = config.get("monitor_index")

# Serial Port Selection
def find_serial_port():
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

# Monitor Selection
def find_monitor():
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

# Serial Connection
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)
    except serial.SerialException:
        print(f"Failed to connect to {SERIAL_PORT}.")

# **Extract Screen Colors**
def get_screen_grid_colors():
    """Captures the screen, divides it into a grid, and extracts colors from each region."""
    with mss.mss() as sct:
        screen_size = sct.monitors[MONITOR_INDEX]
        width, height = screen_size["width"], screen_size["height"]
        screenshot = sct.grab(screen_size)

        # Convert Screenshot to NumPy Array (BGR)
        img_bgr = np.array(screenshot)

        # Convert BGR to RGB before processing
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Enhance Colors
        pil_img = Image.fromarray(img_rgb)
        enhancer = ImageEnhance.Color(pil_img)
        img_rgb = np.array(enhancer.enhance(1.4))  # Increase color contrast

        box_width = width // GRID_COLS
        box_height = height // GRID_ROWS

        grid_colors = []
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x1, y1 = col * box_width, row * box_height
                x2, y2 = x1 + box_width, y1 + box_height
                section = img_rgb[y1:y2, x1:x2]

                avg_color = np.mean(section, axis=(0, 1)).astype(int)
                r, g, b = avg_color[0].item(), avg_color[1].item(), avg_color[2].item()

                # Calculate Perceived Brightness (Luminance Formula)
                brightness = np.sqrt(0.299 * (r**2) + 0.587 * (g**2) + 0.114 * (b**2))  
                
                # Ignore very dark colors
                if brightness > BRIGHTNESS_THRESHOLD:
                    grid_colors.append({"R": r, "G": g, "B": b, "row": row, "col": col})

        return grid_colors

# **Select Most Distinct Colors**
def get_most_distinct_colors(colors, num_colors=NUM_DISTINCT_COLORS):
    """Filters out visually similar colors and selects the most distinct ones."""
    if len(colors) <= num_colors:
        return colors
    
    color_array = np.array([[c["R"], c["G"], c["B"]] for c in colors])

    # Boost warm colors slightly
    weights = np.array([1.5, 1.0, 0.7])  
    weighted_colors = color_array * weights

    dist_matrix = distance.cdist(weighted_colors, weighted_colors, metric="euclidean")
    distinct_scores = np.sum(dist_matrix, axis=1)
    sorted_indices = np.argsort(distinct_scores)[::-1]  # Sort in descending order

    selected_colors = []
    for idx in sorted_indices:
        color = colors[idx]

        # Check if new color is too similar to existing selected colors
        too_similar = any(
            distance.euclidean(
                [color["R"], color["G"], color["B"]],
                [c["R"], c["G"], c["B"]]
            ) < COLOR_SIMILARITY_THRESHOLD for c in selected_colors
        )

        if not too_similar:
            selected_colors.append(color)

        if len(selected_colors) >= num_colors:
            break

    return selected_colors

# **Display Colors in a Window**
def show_grid_colors(colors, selected_colors):
    """Displays the detected colors in an OpenCV window."""
    if not colors:
        print("⚠ No colors detected.")
        return

    rows, cols = GRID_ROWS, GRID_COLS
    block_size = 40  
    img_height = rows * block_size
    img_width = cols * block_size

    color_grid = np.zeros((img_height, img_width, 3), dtype=np.uint8)

    selected_positions = {(c["row"], c["col"], c["R"], c["G"], c["B"]) for c in selected_colors}

    for color in colors:
        row, col = color["row"], color["col"]
        r, g, b = color["R"], color["G"], color["B"]

        x1, y1 = col * block_size, row * block_size
        x2, y2 = x1 + block_size, y1 + block_size

        color_grid[y1:y2, x1:x2] = (b, g, r)  # OpenCV expects BGR

        for (sr, sc, sr_r, sr_g, sr_b) in selected_positions:
            if sr == row and sc == col:
                opposite_color = (255 - sr_b, 255 - sr_g, 255 - sr_r)  
                cv2.line(color_grid, (x1, y1), (x2, y2), opposite_color, 2)
                cv2.line(color_grid, (x1, y2), (x2, y1), opposite_color, 2)

    cv2.imshow("Detected Grid Colors", color_grid)
    cv2.waitKey(1)

# **Stream Colors**
while True:
    colors = get_screen_grid_colors()
    distinct_colors = get_most_distinct_colors(colors)

    print("Detected Colors:", distinct_colors)

    json_data = json.dumps({"LEDColors": distinct_colors})

    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f"Sent to ESP32: {json_data}")

    show_grid_colors(colors, distinct_colors)
    time.sleep(UPDATE_INTERVAL)