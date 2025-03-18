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
GRID_ROWS = 20  
GRID_COLS = 20  
UPDATE_INTERVAL = 0.1  
NUM_DISTINCT_COLORS = 6  
BRIGHTNESS_THRESHOLD = 70  
COLOR_SIMILARITY_THRESHOLD = 25  # LAB color space threshold for color distinction

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

# **Convert RGB to LAB for Better Color Similarity Check**
def rgb_to_lab(color):
    """Convert an RGB color to LAB space for better similarity checking."""
    rgb = np.array([[color]], dtype=np.uint8)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    return lab[0][0]

# **Extract Screen Colors**
def get_screen_grid_colors():
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
        img_rgb = np.array(enhancer.enhance(1.4))  

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

                # Calculate Perceived Brightness
                brightness = np.sqrt(0.299 * (r**2) + 0.587 * (g**2) + 0.114 * (b**2))  
                
                # Ignore very dark colors
                if brightness > BRIGHTNESS_THRESHOLD:
                    grid_colors.append({"R": r, "G": g, "B": b, "row": row, "col": col, "LAB": rgb_to_lab((r, g, b))})

        return grid_colors

# **Select Most Distinct Colors Using LAB Color Space**
def get_most_distinct_colors(colors, num_colors=NUM_DISTINCT_COLORS):
    if len(colors) <= num_colors:
        return colors
    
    selected_colors = []
    for color in colors:
        lab_color = color["LAB"]

        # Ensure new color is visually distinct
        too_similar = any(
            distance.euclidean(lab_color, c["LAB"]) < COLOR_SIMILARITY_THRESHOLD
            for c in selected_colors
        )

        if not too_similar:
            selected_colors.append(color)

        if len(selected_colors) >= num_colors:
            break

    return selected_colors

# **Display Colors in a Window**
def show_grid_colors(colors, selected_colors):
    if not colors:
        print("⚠ No colors detected.")
        return

    rows, cols = GRID_ROWS, GRID_COLS
    block_size = 20  
    img_height = rows * block_size
    img_width = cols * block_size
    led_display_height = 70  

    # Create main grid display
    color_grid = np.zeros((img_height + led_display_height, img_width, 3), dtype=np.uint8)

    selected_positions = {(c["row"], c["col"], c["R"], c["G"], c["B"]) for c in selected_colors}

    for color in colors:
        row, col = color["row"], color["col"]
        r, g, b = color["R"], color["G"], color["B"]

        x1, y1 = col * block_size, row * block_size
        x2, y2 = x1 + block_size, y1 + block_size

        color_grid[y1:y2, x1:x2] = (b, g, r)  

        for (sr, sc, sr_r, sr_g, sr_b) in selected_positions:
            if sr == row and sc == col:
                opposite_color = (255 - sr_b, 255 - sr_g, 255 - sr_r)  
                cv2.line(color_grid, (x1, y1), (x2, y2), opposite_color, 1)
                cv2.line(color_grid, (x1, y2), (x2, y1), opposite_color, 1)

    # Draw label above LED colors
    cv2.rectangle(color_grid, (0, img_height), (img_width, img_height + 20), (0, 0, 0), -1)
    cv2.putText(color_grid, "Colors Sent to the LED", (10, img_height + 15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    # Display the LED color strip at the bottom
    led_block_width = img_width // NUM_DISTINCT_COLORS
    for i, color in enumerate(selected_colors):
        r, g, b = color["R"], color["G"], color["B"]
        led_x1, led_x2 = i * led_block_width, (i + 1) * led_block_width
        color_grid[img_height + 20:img_height + led_display_height, led_x1:led_x2] = (b, g, r)  

    cv2.imshow("Detected Grid Colors", color_grid)
    cv2.waitKey(1)

# **Stream Colors**
while True:
    colors = get_screen_grid_colors()
    distinct_colors = get_most_distinct_colors(colors)

    show_grid_colors(colors, distinct_colors)
    time.sleep(UPDATE_INTERVAL)