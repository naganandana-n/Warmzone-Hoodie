import numpy as np
import sounddevice as sd

# WASAPI Settings
SAMPLERATE = 44100  # Standard audio rate
CHUNK = 1024        # Buffer size
DEVICE_INDEX = None  # Auto-detect default output device

# Detect WASAPI host API
hostapis = sd.query_hostapis()
wasapi_index = None
for i, hostapi in enumerate(hostapis):
    if "WASAPI" in hostapi["name"]:
        wasapi_index = i
        break

if wasapi_index is None:
    print("❌ WASAPI not available on this system!")
    exit()

# Find WASAPI output device
devices = sd.query_devices()
loopback_devices = [i for i, d in enumerate(devices) if d["hostapi"] == wasapi_index and d["max_output_channels"] > 0]

if loopback_devices:
    DEVICE_INDEX = loopback_devices[0]
    print(f"🎧 Using WASAPI Loopback Device: {devices[DEVICE_INDEX]['name']}")
else:
    print("❌ No WASAPI loopback device found!")
    exit()

def get_audio_intensity(indata, frames, time, status):
    """Processes audio input and calculates intensity."""
    if status:
        print(status)

    # Convert audio to intensity using RMS (Root Mean Square)
    intensity = np.sqrt(np.mean(indata**2))

    # Normalize intensity to 0-5 scale
    MAX_INTENSITY = 0.3  # Adjust based on real-world testing
    scaled_intensity = min(5, max(0, (intensity / MAX_INTENSITY) * 5))

    print(f"🎶 Audio Intensity: {round(scaled_intensity, 2)}/5")

# Start capturing system audio
try:
    with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity, dtype='float32', blocksize=CHUNK):
        print("🎵 Streaming audio intensity (0-5 scale)... Press Ctrl+C to stop.")
        while True:
            sd.sleep(100)
except Exception as e:
    print(f"❌ Error: {e}")