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



# this one was the recent one - but delay and port issues [WORKING]

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
import os

CONTROL_JSON_PATH = os.path.join(os.path.dirname(__file__), "control_state.json")
SHUTDOWN_FLAG_PATH = os.path.join(os.path.dirname(__file__), "shutdown_flag.json")

def read_control_state():
    try:
        with open(CONTROL_JSON_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to read control_state.json: {e}")
        return {
            "audio": True,
            "screen": True,
            "mouse": True,
            "sensitivity": 3,
            "heaters": [1, 1, 1],
            "vibration": False,
            "sync_with_audio": False
        }

def was_shutdown_requested():
    try:
        with open(SHUTDOWN_FLAG_PATH, "r") as f:
            data = json.load(f)
            return data.get("shutdown", False)
    except Exception:
        return False

# ** Control Variables**
stop_event = threading.Event()
serial_queue = Queue()
SERIAL_WRITE_DELAY = 0.1  # Adjust sending rate

# ** Find Available Serial Port**
# ** Get Serial Port from selected_port.json**
def get_selected_serial_port():
    try:
        with open(os.path.join(os.path.dirname(__file__), "selected_port.json"), "r") as f:
            data = json.load(f)
            return data.get("port", None)
    except Exception as e:
        print(f" Could not read selected_port.json: {e}")
        return None

SERIAL_PORT = get_selected_serial_port()

ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        ser.flush()  # Clear previous data
        time.sleep(2)
        print(f" Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f" Failed to connect to {SERIAL_PORT}.")
        ser = None


# Store movement data
positions = []
timestamps = []
velocities = []

# Constants
MAX_SPEED = 5000  # Adjust for sensitivity
HISTORY_SIZE = 100  # Use last 100 points for smoothing
DECAY_TIME = 200  # Time for speed to decay to 0
EMA_ALPHA = 0.1  # Smoothing factor for Exponential Moving Average
ACCELERATION_WEIGHT = 1.0  # Reduce acceleration influence
ACCELERATION_LIMIT = 200  # Limit acceleration effect
RAMP_UP_SPEED = 0.5  # Prevents sudden jumps
DECAY_START_TIME = 60  # **Start decay after 60 seconds of no movement**

# Track last computed speed
smoothed_speed = 0
last_update_time = time.time()


def on_move(x, y):
    """Tracks mouse movement, updates speed calculations."""
    global positions, timestamps, velocities, last_update_time

    # Store position and timestamp
    positions.append((x, y))
    timestamps.append(time.time())

    # Keep only the last HISTORY_SIZE points
    if len(positions) > HISTORY_SIZE:
        positions.pop(0)
        timestamps.pop(0)
        velocities.pop(0) if len(velocities) > 0 else None  # Trim velocity list

    last_update_time = time.time()  # Update last movement time


def calculate_scaled_speed():
    """Calculates smoothed speed (0 to 5), considering acceleration & decay after 60 sec."""
    global smoothed_speed

    if len(positions) < 2:
        return smoothed_speed  # Maintain previous speed if no movement

    distances = []
    times = []
    accel_values = []

    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        distance = np.sqrt(dx**2 + dy**2)

        dt = timestamps[i] - timestamps[i - 1]
        if dt > 0:
            speed = distance / dt  # Speed = Distance / Time
            distances.append(speed)

            if len(velocities) > 0:
                accel = abs(speed - velocities[-1]) / dt  # Acceleration = Change in speed / Time
                accel_values.append(min(accel, ACCELERATION_LIMIT))  # Limit acceleration effect

            velocities.append(speed)

    avg_speed = np.mean(distances) if distances else 0
    avg_accel = np.mean(accel_values) if accel_values else 0

    # **Boost speed using acceleration (but limit max effect)**
    boosted_speed = avg_speed + (ACCELERATION_WEIGHT * avg_accel)

    # Normalize speed to 0-5 range
    scaled_speed = min(5, max(0, (boosted_speed / MAX_SPEED) * 5))

    # **Apply Exponential Moving Average (EMA) for smoother transitions**
    new_smoothed_speed = (EMA_ALPHA * scaled_speed) + ((1 - EMA_ALPHA) * smoothed_speed)

    # **Prevent Instant Jumps**
    if new_smoothed_speed > smoothed_speed:
        new_smoothed_speed = min(smoothed_speed + RAMP_UP_SPEED, new_smoothed_speed)

    smoothed_speed = new_smoothed_speed

    # **Apply gradual decay if no movement detected for 1 minute**
    time_since_last_move = time.time() - last_update_time

    if time_since_last_move > DECAY_START_TIME:
        decay_factor = max(0, 1 - ((time_since_last_move - DECAY_START_TIME) / DECAY_TIME))
        smoothed_speed *= decay_factor  # Gradually decrease speed

    return round(smoothed_speed, 2)


# **Start listening to mouse movement**
mouse_listener = mouse.Listener(on_move=on_move)
mouse_listener.start()

# ** Audio Processing**
DEVICE_INDEX = None
SAMPLERATE = 44100
MAX_INTENSITY = 0.3
intensity_buffer = deque(maxlen=10)
audio_brightness = 0

def get_audio_intensity(indata, frames, time, status):
    """Process audio intensity and update brightness."""
    global audio_brightness
    intensity = np.sqrt(np.mean(indata**2))
    brightness = min(255, max(0, int((intensity / MAX_INTENSITY) * 255)))
    intensity_buffer.append(brightness)
    audio_brightness = int(np.mean(intensity_buffer))

# ** Screen Color Processing**
GRID_ROWS, GRID_COLS = 10, 10
BRIGHTNESS_THRESHOLD = 60
NUM_DISTINCT_COLORS = 6
COLOR_SIMILARITY_THRESHOLD = 80

def get_screen_grid_colors():
    """Capture screen colors and extract dominant ones."""
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
                    grid_colors.append({"R": r, "G": g, "B": b})

        return grid_colors[:NUM_DISTINCT_COLORS]

def send_data():
    """Send merged JSON data for screen, audio, and mouse updates at a fixed rate."""
    while not stop_event.is_set():
        # Read control state
        try:
            with open("control_state.json", "r") as f:
                control = json.load(f)
        except Exception as e:
            print(f"Failed to read control_state.json: {e}")
            control = {}

        json_data = {}

        # Conditionally include data based on UI toggle
        if control.get("screen", True):
            colors = get_screen_grid_colors()
            json_data["LEDColors"] = colors

        if control.get("audio", True):
            json_data["Brightness"] = audio_brightness

        if control.get("mouse", True):
            json_data["MouseSpeed"] = calculate_scaled_speed()

        # Future support
        json_data["sensitivity"] = control.get("sensitivity", 3)
        json_data["heaters"] = control.get("heaters", [1, 1, 1])
        json_data["vibration"] = control.get("vibration", False)
        json_data["sync_with_audio"] = control.get("sync_with_audio", False)

        # Send to ESP32
        json_str = json.dumps(json_data)
        serial_queue.put(json_str)
        print(f" Sending: {json_str}")

        time.sleep(SERIAL_WRITE_DELAY)

# ** Serial Write Thread**
def serial_write_loop():
    """Continuously send data to ESP32 at a controlled rate."""
    while not stop_event.is_set():
        try:
            json_data = serial_queue.get(timeout=0.5)
            if ser:
                ser.write(f"{json_data}\n".encode())  # Send to ESP32
                print(f" Data sent: {json_data}")  # Confirm data sent
                time.sleep(SERIAL_WRITE_DELAY)  # Prevent overflow
        except Empty:
            continue
        except serial.SerialTimeoutException:
            print(" Serial write timeout, skipping data")

# **🔹 Run All Features in Parallel**
def main_loop():
    """Main loop to process audio and start screen, mouse, and serial threads."""
    try:
        with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
            threading.Thread(target=send_data, daemon=True).start()
            threading.Thread(target=serial_write_loop, daemon=True).start()

            while not stop_event.is_set():
                if was_shutdown_requested():
                    print(" Shutdown requested via shutdown_flag.json")
                    stop_event.set()
                    break
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n Exiting program... (Ctrl + C detected)")
        stop_event.set()

    finally:
        if ser:
            ser.close()
        time.sleep(1)
        exit(0)
    
# **🔹 Run the main function**
if __name__ == "__main__":
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    main_thread.join()
'''

# edited version of the above:

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
import os

# Track how many messages have been sent
flush_counter = 0

CONTROL_JSON_PATH = os.path.join(os.path.dirname(__file__), "control_state.json")
SHUTDOWN_FLAG_PATH = os.path.join(os.path.dirname(__file__), "shutdown_flag.json")

def read_control_state():
    try:
        with open(CONTROL_JSON_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to read control_state.json: {e}")
        return {
            "audio": True,
            "screen": True,
            "mouse": True,
            "sensitivity": 3,
            "heaters": [1, 1, 1],
            "vibration": False,
            "sync_with_audio": False
        }

def was_shutdown_requested():
    try:
        with open(SHUTDOWN_FLAG_PATH, "r") as f:
            data = json.load(f)
            return data.get("shutdown", False)
    except Exception:
        return False

# ** Control Variables**
stop_event = threading.Event()
serial_queue = Queue()
SERIAL_WRITE_DELAY = 0.1  # Adjust sending rate

# ** Find Available Serial Port**
# ** Get Serial Port from selected_port.json**
def get_selected_serial_port():
    try:
        with open(os.path.join(os.path.dirname(__file__), "selected_port.json"), "r") as f:
            data = json.load(f)
            return data.get("port", None)
    except Exception as e:
        print(f" Could not read selected_port.json: {e}")
        return None

SERIAL_PORT = get_selected_serial_port()

ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, 115200, timeout=1)
        ser.flush()  # Clear previous data
        time.sleep(2)
        print(f" Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f" Failed to connect to {SERIAL_PORT}.")
        ser = None


# Store movement data
positions = []
timestamps = []
velocities = []

# Constants
MAX_SPEED = 5000  # Adjust for sensitivity
HISTORY_SIZE = 100  # Use last 100 points for smoothing
DECAY_TIME = 200  # Time for speed to decay to 0
EMA_ALPHA = 0.1  # Smoothing factor for Exponential Moving Average
ACCELERATION_WEIGHT = 1.0  # Reduce acceleration influence
ACCELERATION_LIMIT = 200  # Limit acceleration effect
RAMP_UP_SPEED = 0.5  # Prevents sudden jumps
DECAY_START_TIME = 60  # **Start decay after 60 seconds of no movement**

# Track last computed speed
smoothed_speed = 0
last_update_time = time.time()


def on_move(x, y):
    """Tracks mouse movement, updates speed calculations."""
    global positions, timestamps, velocities, last_update_time

    # Store position and timestamp
    positions.append((x, y))
    timestamps.append(time.time())

    # Keep only the last HISTORY_SIZE points
    if len(positions) > HISTORY_SIZE:
        positions.pop(0)
        timestamps.pop(0)
        velocities.pop(0) if len(velocities) > 0 else None  # Trim velocity list

    last_update_time = time.time()  # Update last movement time


def calculate_scaled_speed():
    """Calculates smoothed speed (0 to 5), considering acceleration & decay after 60 sec."""
    global smoothed_speed

    if len(positions) < 2:
        return smoothed_speed  # Maintain previous speed if no movement

    distances = []
    times = []
    accel_values = []

    for i in range(1, len(positions)):
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        distance = np.sqrt(dx**2 + dy**2)

        dt = timestamps[i] - timestamps[i - 1]
        if dt > 0:
            speed = distance / dt  # Speed = Distance / Time
            distances.append(speed)

            if len(velocities) > 0:
                accel = abs(speed - velocities[-1]) / dt  # Acceleration = Change in speed / Time
                accel_values.append(min(accel, ACCELERATION_LIMIT))  # Limit acceleration effect

            velocities.append(speed)

    avg_speed = np.mean(distances) if distances else 0
    avg_accel = np.mean(accel_values) if accel_values else 0

    # **Boost speed using acceleration (but limit max effect)**
    boosted_speed = avg_speed + (ACCELERATION_WEIGHT * avg_accel)

    # Normalize speed to 0-5 range
    scaled_speed = min(5, max(0, (boosted_speed / MAX_SPEED) * 5))

    # **Apply Exponential Moving Average (EMA) for smoother transitions**
    new_smoothed_speed = (EMA_ALPHA * scaled_speed) + ((1 - EMA_ALPHA) * smoothed_speed)

    # **Prevent Instant Jumps**
    if new_smoothed_speed > smoothed_speed:
        new_smoothed_speed = min(smoothed_speed + RAMP_UP_SPEED, new_smoothed_speed)

    smoothed_speed = new_smoothed_speed

    # **Apply gradual decay if no movement detected for 1 minute**
    time_since_last_move = time.time() - last_update_time

    if time_since_last_move > DECAY_START_TIME:
        decay_factor = max(0, 1 - ((time_since_last_move - DECAY_START_TIME) / DECAY_TIME))
        smoothed_speed *= decay_factor  # Gradually decrease speed

    return round(smoothed_speed, 2)


# **Start listening to mouse movement**
mouse_listener = mouse.Listener(on_move=on_move)
mouse_listener.start()

# ** Audio Processing**
DEVICE_INDEX = None
SAMPLERATE = 44100
MAX_INTENSITY = 0.3
intensity_buffer = deque(maxlen=10)
audio_brightness = 0

def get_audio_intensity(indata, frames, time, status):
    """Process audio intensity and update brightness."""
    global audio_brightness
    intensity = np.sqrt(np.mean(indata**2))
    brightness = min(255, max(0, int((intensity / MAX_INTENSITY) * 255)))
    intensity_buffer.append(brightness)
    audio_brightness = int(np.mean(intensity_buffer))

# ** Screen Color Processing**
GRID_ROWS, GRID_COLS = 10, 10
BRIGHTNESS_THRESHOLD = 60
NUM_DISTINCT_COLORS = 6
COLOR_SIMILARITY_THRESHOLD = 80

def get_screen_grid_colors():
    """Capture screen colors and extract dominant ones."""
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
                    grid_colors.append({"R": r, "G": g, "B": b})

        return grid_colors[:NUM_DISTINCT_COLORS]

def send_data():
    """Send merged JSON data for screen, audio, and mouse updates at a fixed rate."""
    while not stop_event.is_set():
        # Read control state
        try:
            with open("control_state.json", "r") as f:
                control = json.load(f)
        except Exception as e:
            print(f"Failed to read control_state.json: {e}")
            control = {}

        json_data = {}

        # Conditionally include data based on UI toggle
        if control.get("screen", True):
            colors = get_screen_grid_colors()
            json_data["LEDColors"] = colors

        if control.get("audio", True):
            json_data["Brightness"] = audio_brightness

        if control.get("mouse", True):
            json_data["MouseSpeed"] = calculate_scaled_speed()

        # Future support
        json_data["sensitivity"] = control.get("sensitivity", 3)
        json_data["heaters"] = control.get("heaters", [1, 1, 1])
        json_data["vibration"] = control.get("vibration", False)
        json_data["sync_with_audio"] = control.get("sync_with_audio", False)

        # Send to ESP32
        json_str = json.dumps(json_data)
        serial_queue.put(json_str)
        # Increment counter and flush every 1000 messages
        flush_counter += 1
        if flush_counter >= 1000:
            if ser:
                ser.flush()
                print("🔄 Serial buffer flushed.")
            flush_counter = 0
        print(f" Sending: {json_str}")
        time.sleep(SERIAL_WRITE_DELAY)

# ** Serial Write Thread**
def serial_write_loop():
    """Continuously send data to ESP32 at a controlled rate."""
    while not stop_event.is_set():
        try:
            json_data = serial_queue.get(timeout=0.5)
            if ser:
                ser.write(f"{json_data}\n".encode())  # Send to ESP32
                print(f" Data sent: {json_data}")  # Confirm data sent
                time.sleep(SERIAL_WRITE_DELAY)  # Prevent overflow
        except Empty:
            continue
        except serial.SerialTimeoutException:
            print(" Serial write timeout, skipping data")

# **🔹 Run All Features in Parallel**
def main_loop():
    """Main loop to process audio and start screen, mouse, and serial threads."""
    try:
        with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
            threading.Thread(target=send_data, daemon=True).start()
            threading.Thread(target=serial_write_loop, daemon=True).start()

            while not stop_event.is_set():
                if was_shutdown_requested():
                    print(" Shutdown requested via shutdown_flag.json")
                    stop_event.set()
                    break
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n Exiting program... (Ctrl + C detected)")
        stop_event.set()

    finally:
        if ser:
            ser.close()
        time.sleep(1)
        exit(0)
    
# **🔹 Run the main function**
if __name__ == "__main__":
    main_thread = threading.Thread(target=main_loop, daemon=True)
    main_thread.start()
    main_thread.join()