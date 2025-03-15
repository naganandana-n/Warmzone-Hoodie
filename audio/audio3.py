import sounddevice as sd
import numpy as np

# Use VB-Audio Virtual Cable as the input device
DEVICE_NAME = "CABLE Output"  # This is the name of VB-Audio Virtual Cable's output
SAMPLERATE = 44100  # Standard sample rate
CHUNK = 1024  # Buffer size

# Find the index of VB-Audio Virtual Cable
def get_virtual_cable_index():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if DEVICE_NAME in device["name"] and device["max_input_channels"] > 0:
            return i
    return None

DEVICE_INDEX = get_virtual_cable_index()

if DEVICE_INDEX is None:
    print("❌ VB-Audio Virtual Cable not found. Ensure it's installed and set as default.")
    exit(1)

print(f"🎤 Using device: {DEVICE_NAME} (Index: {DEVICE_INDEX})")

def get_audio_intensity(indata, frames, time, status):
    """Processes system audio input and calculates intensity."""
    if status:
        print(status)
    # Compute RMS (Root Mean Square) for loudness detection
    intensity = np.sqrt(np.mean(indata**2))
    
    # Normalize intensity to a 0-5 scale
    MAX_INTENSITY = 0.3  # Adjust based on real-world testing
    scaled_intensity = min(5, max(0, (intensity / MAX_INTENSITY) * 5))
    
    print(f"🎶 Audio Intensity: {round(scaled_intensity, 2)}/5")

# Start streaming audio from VB-Audio Virtual Cable
try:
    with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
        print("🎵 Streaming system audio intensity... Press Ctrl+C to stop.")
        while True:
            sd.sleep(100)
except Exception as e:
    print(f"❌ Error: {e}")