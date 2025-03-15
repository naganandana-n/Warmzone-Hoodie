# take avg of last 10 readings to smooth out the audio

import sounddevice as sd
import numpy as np
import serial
import json
import time
import serial.tools.list_ports
from collections import deque  # Used for rolling buffer

# 🎵 Audio Capture Settings
DEVICE_INDEX = None  # Set to None for default loopback (VB Cable)
SAMPLERATE = 44100   # Standard audio rate
CHUNK = 1024         # Buffer size
MAX_INTENSITY = 0.3  # Max audio intensity for scaling
SERIAL_BAUDRATE = 115200  # ESP32 baud rate
ROLLING_WINDOW = 10  # Number of past values to average

# 🔄 Rolling buffer to store last 10 intensity values
intensity_buffer = deque(maxlen=ROLLING_WINDOW)

# 📡 Detect Available Serial Ports
def find_serial_port():
    """Finds and lists available serial ports for ESP32 connection."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No serial ports detected. Check your ESP32 connection.")
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
                print("❌ Invalid selection. Choose a valid port number.")
        except ValueError:
            print("❌ Please enter a number.")

# 📡 Connect to ESP32
SERIAL_PORT = find_serial_port()
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1)
        time.sleep(2)  # Allow ESP32 to initialize
        print(f"✅ Connected to ESP32 on {SERIAL_PORT}")
    except serial.SerialException:
        print(f"❌ Failed to connect to {SERIAL_PORT}. Check your ESP32 connection.")

# 🎵 Audio Processing Function
def get_audio_intensity(indata, frames, time, status):
    """Processes audio input, averages the last 10 readings, and sends smoothed intensity to ESP32."""
    if status:
        print(status)

    # Compute RMS (Root Mean Square) for audio intensity
    intensity = np.sqrt(np.mean(indata**2))

    # Normalize intensity to 0-255 for LED control
    brightness = min(255, max(0, int((intensity / MAX_INTENSITY) * 255)))

    # Add new value to rolling buffer
    intensity_buffer.append(brightness)

    # Compute the smoothed average of last 10 readings
    avg_brightness = int(np.mean(intensity_buffer))

    # Create JSON payload
    json_data = json.dumps({"AudioIntensity": avg_brightness})

    # Send JSON to ESP32
    if ser:
        ser.write(f"{json_data}\n".encode())
        print(f"📡 Sent to ESP32: {json_data} (Smoothed)")

# 🎵 Start Audio Stream
try:
    with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
        print("\n🎵 Streaming Smoothed Audio Intensity to ESP32... Press Ctrl+C to stop.")
        while True:
            sd.sleep(50)  # Update every 50ms (fast response)
except Exception as e:
    print(f"❌ Error: {e}")