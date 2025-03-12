import sounddevice as sd
import numpy as np

# Audio settings
DEVICE_INDEX = None  # Auto-select system default loopback
SAMPLERATE = 44100   # Standard audio rate
CHUNK = 1024         # Buffer size

def get_audio_intensity(indata, frames, time, status):
    """Callback function to process audio input and calculate intensity."""
    if status:
        print(status)
    # Convert audio to intensity using RMS (Root Mean Square)
    intensity = np.sqrt(np.mean(indata**2))
    
    # Normalize intensity to 0-5 scale
    MAX_INTENSITY = 0.3  # Adjust based on real-world testing
    scaled_intensity = min(5, max(0, (intensity / MAX_INTENSITY) * 5))
    
    print(f"🎶 Audio Intensity: {round(scaled_intensity, 2)}/5")

# List all available audio devices
print("\n🔍 Checking Available Audio Devices...\n")
devices = sd.query_devices()
print(devices)

# Find a loopback device (default)
try:
    with sd.InputStream(device=DEVICE_INDEX, channels=1, samplerate=SAMPLERATE, callback=get_audio_intensity):
        print("🎵 Streaming audio intensity (0-5 scale)... Press Ctrl+C to stop.")
        while True:
            sd.sleep(100)
except Exception as e:
    print(f"❌ Error: {e}")