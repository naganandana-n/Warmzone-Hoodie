import sounddevice as sd

# Get host API details
hostapis = sd.query_hostapis()

print("🔍 Available Host APIs:")
for i, api in enumerate(hostapis):
    print(f"[{i}] {api}")

# Get device details
devices = sd.query_devices()

print("\n🎧 Available Audio Devices:")
for i, device in enumerate(devices):
    print(f"[{i}] {device}")