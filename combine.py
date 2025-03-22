'''

# first version - correct individual modules

import time
import json
import threading
import serial
import serial.tools.list_ports
import numpy as np
import sounddevice as sd
import mss
import cv2
from pynput import mouse
from collections import deque
from PIL import Image, ImageEnhance
from scipy.spatial import distance

# **📡 Find Available Serial Port**
def find_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No serial ports detected.")
        return None

    print("\n🔍 Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    while True:
        try:
            choice = int(input("\n🎯 Select a port number: ")) - 1
            if 0 <= choice < len(ports):
                return ports[choice].device
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Enter a valid number.")

SERIAL_PORT = find_serial_port()
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)
        print(f"✅ Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f"❌ Failed to connect to {SERIAL_PORT}.")

# **📌 Mouse Tracking**
positions, timestamps, velocities = [], [], []
MAX_SPEED = 5000
HISTORY_SIZE = 100
DECAY_TIME = 200
EMA_ALPHA = 0.1
ACCELERATION_WEIGHT = 1.0
ACCELERATION_LIMIT = 200
RAMP_UP_SPEED = 0.5
DECAY_START_TIME = 60
smoothed_speed = 0
last_update_time = time.time()

def on_move(x, y):
    global positions, timestamps, velocities, last_update_time
    positions.append((x, y))
    timestamps.append(time.time())

    if len(positions) > HISTORY_SIZE:
        positions.pop(0)
        timestamps.pop(0)
        if velocities:
            velocities.pop(0)

    last_update_time = time.time()

mouse_listener = mouse.Listener(on_move=on_move)
mouse_listener.start()

def calculate_mouse_speed():
    global smoothed_speed
    if len(positions) < 2:
        return smoothed_speed

    distances = []
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        distance = np.sqrt(dx**2 + dy**2)
        dt = timestamps[i] - timestamps[i - 1]
        if dt > 0:
            speed = distance / dt
            distances.append(speed)

    avg_speed = np.mean(distances) if distances else 0
    scaled_speed = min(5, max(0, (avg_speed / MAX_SPEED) * 5))
    smoothed_speed = (EMA_ALPHA * scaled_speed) + ((1 - EMA_ALPHA) * smoothed_speed)

    if time.time() - last_update_time > DECAY_START_TIME:
        decay_factor = max(0, 1 - ((time.time() - last_update_time - DECAY_START_TIME) / DECAY_TIME))
        smoothed_speed *= decay_factor

    return round(smoothed_speed, 2)

# **🎵 Audio Processing**
DEVICE_INDEX = None
SAMPLERATE = 44100
MAX_INTENSITY = 0.3
ROLLING_WINDOW = 10
intensity_buffer = deque(maxlen=ROLLING_WINDOW)

def get_audio_intensity(indata, frames, time, status):
    intensity = np.sqrt(np.mean(indata**2))
    brightness = min(255, max(0, int((intensity / MAX_INTENSITY) * 255)))
    intensity_buffer.append(brightness)
    avg_brightness = int(np.mean(intensity_buffer))

    if ser:
        json_data = json.dumps({"AudioIntensity": avg_brightness})
        ser.write(f"{json_data}\n".encode())

# **🎨 Screen Color Processing**
GRID_ROWS, GRID_COLS = 10, 10
UPDATE_INTERVAL = 0.1
NUM_DISTINCT_COLORS = 6
BRIGHTNESS_THRESHOLD = 60
COLOR_SIMILARITY_THRESHOLD = 80

def get_screen_grid_colors():
    with mss.mss() as sct:
        screen = sct.grab(sct.monitors[1])
        img = np.array(screen)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        enhancer = ImageEnhance.Color(pil_img)
        img_rgb = np.array(enhancer.enhance(1.4))

        box_width = img_rgb.shape[1] // GRID_COLS
        box_height = img_rgb.shape[0] // GRID_ROWS
        grid_colors = []

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x1, y1 = col * box_width, row * box_height
                x2, y2 = x1 + box_width, y1 + box_height
                section = img_rgb[y1:y2, x1:x2]

                avg_color = np.mean(section, axis=(0, 1)).astype(int)
                r, g, b = avg_color.tolist()
                brightness = np.sqrt(0.299 * (r**2) + 0.587 * (g**2) + 0.114 * (b**2))

                if brightness > BRIGHTNESS_THRESHOLD:
                    grid_colors.append({"R": r, "G": g, "B": b, "row": row, "col": col})

        return grid_colors

def get_most_distinct_colors(colors):
    if len(colors) <= NUM_DISTINCT_COLORS:
        return colors

    selected_colors = []
    for color in colors:
        if not any(
            distance.euclidean([color["R"], color["G"], color["B"]], [c["R"], c["G"], c["B"]])
            < COLOR_SIMILARITY_THRESHOLD
            for c in selected_colors
        ):
            selected_colors.append(color)

        if len(selected_colors) >= NUM_DISTINCT_COLORS:
            break

    return selected_colors

def screen_loop():
    while True:
        colors = get_screen_grid_colors()
        distinct_colors = get_most_distinct_colors(colors)

        json_data = json.dumps({"LEDColors": distinct_colors})
        if ser:
            ser.write(f"{json_data}\n".encode())

        time.sleep(UPDATE_INTERVAL)

# **🔹 Run All Features in Parallel**
def main_loop():
    try:
        with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
            screen_thread = threading.Thread(target=screen_loop, daemon=True)
            screen_thread.start()

            while True:
                mouse_speed = calculate_mouse_speed()
                json_data = json.dumps({"MouseSpeed": mouse_speed})

                if ser:
                    ser.write(f"{json_data}\n".encode())

                time.sleep(0.1)
    except Exception as e:
        print(f"❌ Error: {e}")

# **🔹 Run the main function**
if __name__ == "__main__":
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    main_thread.join()

'''

import time
import json
import threading
import serial
import serial.tools.list_ports
import numpy as np
import sounddevice as sd
import mss
import cv2
from pynput import mouse
from collections import deque
from queue import Queue, Empty
from PIL import Image, ImageEnhance
from scipy.spatial import distance

# **🔹 Control Variables**
stop_event = threading.Event()
serial_queue = Queue()
SERIAL_WRITE_DELAY = 0.2  # Limit ESP32 data rate to every 200ms

# **📡 Find Available Serial Port**
def find_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No serial ports detected.")
        return None

    print("\n🔍 Available Serial Ports:")
    for i, port in enumerate(ports):
        print(f"  [{i+1}] {port.device} - {port.description}")

    while True:
        try:
            choice = int(input("\n🎯 Select a port number: ")) - 1
            if 0 <= choice < len(ports):
                return ports[choice].device
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Enter a valid number.")

SERIAL_PORT = find_serial_port()
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        time.sleep(2)
        print(f"✅ Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f"❌ Failed to connect to {SERIAL_PORT}.")
        ser = None

# **📌 Mouse Tracking**
positions, timestamps, velocities = [], [], []
MAX_SPEED = 5000
HISTORY_SIZE = 100
DECAY_TIME = 200
EMA_ALPHA = 0.1
ACCELERATION_WEIGHT = 1.0
ACCELERATION_LIMIT = 200
RAMP_UP_SPEED = 0.5
DECAY_START_TIME = 60
smoothed_speed = 0
last_update_time = time.time()

def on_move(x, y):
    global positions, timestamps, velocities, last_update_time
    positions.append((x, y))
    timestamps.append(time.time())

    if len(positions) > HISTORY_SIZE:
        positions.pop(0)
        timestamps.pop(0)
        if velocities:
            velocities.pop(0)

    last_update_time = time.time()

mouse_listener = mouse.Listener(on_move=on_move)
mouse_listener.start()

def calculate_mouse_speed():
    global smoothed_speed
    if len(positions) < 2:
        return smoothed_speed

    distances = []
    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        distance = np.sqrt(dx**2 + dy**2)
        dt = timestamps[i] - timestamps[i - 1]
        if dt > 0:
            speed = distance / dt
            distances.append(speed)

    avg_speed = np.mean(distances) if distances else 0
    scaled_speed = min(5, max(0, (avg_speed / MAX_SPEED) * 5))
    smoothed_speed = (EMA_ALPHA * scaled_speed) + ((1 - EMA_ALPHA) * smoothed_speed)

    if time.time() - last_update_time > DECAY_START_TIME:
        decay_factor = max(0, 1 - ((time.time() - last_update_time - DECAY_START_TIME) / DECAY_TIME))
        smoothed_speed *= decay_factor

    return round(smoothed_speed, 2)

# **🎵 Audio Processing**
DEVICE_INDEX = None
SAMPLERATE = 44100
MAX_INTENSITY = 0.3
ROLLING_WINDOW = 10
intensity_buffer = deque(maxlen=ROLLING_WINDOW)

def get_audio_intensity(indata, frames, time, status):
    intensity = np.sqrt(np.mean(indata**2))
    brightness = min(255, max(0, int((intensity / MAX_INTENSITY) * 255)))
    intensity_buffer.append(brightness)
    avg_brightness = int(np.mean(intensity_buffer))

    json_data = json.dumps({"AudioIntensity": avg_brightness})
    serial_queue.put(json_data)  # Add to queue instead of writing immediately

# **🎨 Screen Color Processing**
GRID_ROWS, GRID_COLS = 10, 10
UPDATE_INTERVAL = 0.1
NUM_DISTINCT_COLORS = 6
BRIGHTNESS_THRESHOLD = 60
COLOR_SIMILARITY_THRESHOLD = 80

def get_screen_grid_colors():
    with mss.mss() as sct:
        screen = sct.grab(sct.monitors[1])
        img = np.array(screen)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        enhancer = ImageEnhance.Color(pil_img)
        img_rgb = np.array(enhancer.enhance(1.4))

        box_width = img_rgb.shape[1] // GRID_COLS
        box_height = img_rgb.shape[0] // GRID_ROWS
        grid_colors = []

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x1, y1 = col * box_width, row * box_height
                x2, y2 = x1 + box_width, y1 + box_height
                section = img_rgb[y1:y2, x1:x2]

                avg_color = np.mean(section, axis=(0, 1)).astype(int)
                r, g, b = avg_color.tolist()
                brightness = np.sqrt(0.299 * (r**2) + 0.587 * (g**2) + 0.114 * (b**2))

                if brightness > BRIGHTNESS_THRESHOLD:
                    grid_colors.append({"R": r, "G": g, "B": b, "row": row, "col": col})

        return grid_colors

def get_most_distinct_colors(colors):
    if len(colors) <= NUM_DISTINCT_COLORS:
        return colors

    selected_colors = []
    for color in colors:
        if not any(
            distance.euclidean([color["R"], color["G"], color["B"]], [c["R"], c["G"], c["B"]])
            < COLOR_SIMILARITY_THRESHOLD
            for c in selected_colors
        ):
            selected_colors.append(color)

        if len(selected_colors) >= NUM_DISTINCT_COLORS:
            break

    return selected_colors

def screen_loop():
    while not stop_event.is_set():
        colors = get_screen_grid_colors()
        distinct_colors = get_most_distinct_colors(colors)

        json_data = json.dumps({"LEDColors": distinct_colors})
        serial_queue.put(json_data)

        time.sleep(UPDATE_INTERVAL)

# **📡 Serial Write Thread**
def serial_write_loop():
    while not stop_event.is_set():
        try:
            json_data = serial_queue.get(timeout=0.5)  # Get data from queue
            if ser:
                ser.write(f"{json_data}\n".encode())  # Send to ESP32
                time.sleep(SERIAL_WRITE_DELAY)  # Prevent data flood
        except Empty:
            continue  # No data, just continue loop
        except serial.SerialTimeoutException:
            print("❌ Serial write timeout, skipping data")

# **🔹 Run All Features in Parallel**
def main_loop():
    try:
        with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
            threading.Thread(target=screen_loop, daemon=True).start()
            threading.Thread(target=serial_write_loop, daemon=True).start()

            while not stop_event.is_set():
                mouse_speed = calculate_mouse_speed()
                json_data = json.dumps({"MouseSpeed": mouse_speed})
                serial_queue.put(json_data)

                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🚪 Exiting program... (Ctrl + C detected)")
        stop_event.set()
        if ser:
            ser.close()
        time.sleep(0.5)  # Let threads exit
        exit(0)

# **🔹 Run the main function**
if __name__ == "__main__":
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    main_thread.join()