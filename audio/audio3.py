import sounddevice as sd

# Get all host APIs
hostapis = sd.query_hostapis()

# Find the index for WASAPI
wasapi_index = None
for i, api in enumerate(hostapis):
    if "WASAPI" in api["name"]:  # Check if WASAPI exists
        wasapi_index = i
        break

if wasapi_index is None:
    print("❌ WASAPI not found on this system!")
    exit()

# Get all devices
devices = sd.query_devices()

# Find a valid loopback device
loopback_devices = [
    i for i, d in enumerate(devices) if d["hostapi"] == wasapi_index and d["max_input_channels"] > 0
]

if loopback_devices:
    DEVICE_INDEX = loopback_devices[0]  # Select the first available loopback device
    print(f"🎧 Using WASAPI Loopback Device: {devices[DEVICE_INDEX]['name']}")
else:
    print("❌ No WASAPI loopback device found!")
    exit()