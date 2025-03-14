import sounddevice as sd
import numpy as np

# Auto-detect system loopback device
def find_loopback_device():
    """Finds the system loopback device for capturing internal audio."""
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if "loopback" in device["name"].lower() or "stereo mix" in device["name"].lower():
            print(f"✅ Found Loopback Device: {device['name']} (Index {idx})")
            return idx
    print("❌ No loopback device found! Defaulting to microphone.")
    return None

# Detect the correct device
DEVICE_INDEX = find_loopback_device()

# Audio settings
SAMPLERATE = 44100
CHUNK = 1024

def get_audio_intensity(indata, frames, time, status):
    """Processes audio input and calculates intensity."""
    if status:
        print(status)
    intensity = np.sqrt(np.mean(indata**2))
    MAX_INTENSITY = 0.3
    scaled_intensity = min(5, max(0, (intensity / MAX_INTENSITY) * 5))
    print(f"🎶 Audio Intensity: {round(scaled_intensity, 2)}/5")

# Start streaming audio intensity from system loopback
try:
    with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
        print("🎵 Streaming audio intensity (0-5 scale)... Press Ctrl+C to stop.")
        while True:
            sd.sleep(100)
except Exception as e:
    print(f"❌ Error: {e}")