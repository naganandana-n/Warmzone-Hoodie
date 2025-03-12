import pyaudio
import numpy as np

# Windows WASAPI Loopback settings
FORMAT = pyaudio.paInt16  # 16-bit audio
CHANNELS = 2  # Stereo
RATE = 44100  # Sampling rate
CHUNK = 1024  # Buffer size

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Find the system's output audio device (Loopback)
def get_loopback_device():
    for i in range(audio.get_device_count()):
        dev = audio.get_device_info_by_index(i)
        if "Loopback" in dev["name"]:  # Look for Loopback devices
            return i
    return None

loopback_device = get_loopback_device()

if loopback_device is None:
    print("Error: No loopback device found. Enable Stereo Mix in Sound Settings.")
    exit(1)

# Open a loopback audio stream (captures system audio)
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK, input_device_index=loopback_device)

def get_audio_intensity():
    """Reads system audio and calculates intensity"""
    data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
    intensity = np.sqrt(np.mean(data**2))  # RMS (Root Mean Square)
    
    # Normalize intensity to a 0-5 scale
    MAX_INTENSITY = 3000  # Adjust based on real-world testing
    scaled_intensity = min(5, max(0, (intensity / MAX_INTENSITY) * 5))
    
    return round(scaled_intensity, 2)

# Stream audio intensity
print("Streaming audio intensity (0-5 scale)...")
while True:
    intensity = get_audio_intensity()
    print(f"Audio Intensity: {intensity}/5")