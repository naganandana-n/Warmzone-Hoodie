from pynput import mouse
import time
import numpy as np

# Store movement data
positions = []
timestamps = []
MAX_SPEED = 5000  # Adjust for sensitivity
HISTORY_SIZE = 100  # Use only the last 30 points

def on_move(x, y):
    global positions, timestamps

    # Store position and timestamp
    positions.append((x, y))
    timestamps.append(time.time())

    # Keep only the last 30 points
    if len(positions) > HISTORY_SIZE:
        positions.pop(0)
        timestamps.pop(0)

def calculate_scaled_speed():
    """Calculate the scaled speed (0 to 5) of the mouse movement."""
    if len(positions) < 2:
        return 0  # No movement

    distances = []
    times = []

    for i in range(1, len(positions)):
        # Compute Euclidean distance between consecutive points
        dx = positions[i][0] - positions[i - 1][0]
        dy = positions[i][1] - positions[i - 1][1]
        distance = np.sqrt(dx**2 + dy**2)

        # Compute time difference
        dt = timestamps[i] - timestamps[i - 1]

        if dt > 0:
            distances.append(distance / dt)  # Speed = Distance / Time

    avg_speed = np.mean(distances) if distances else 0

    # Normalize speed to 0-5 range
    scaled_speed = min(5, max(0, (avg_speed / MAX_SPEED) * 5))

    # **Reset speed to 0 if no movement for 0.5 seconds**
    if time.time() - timestamps[-1] > 0.5:
        return 0

    return round(scaled_speed, 2)

# Start listening to mouse movement
listener = mouse.Listener(on_move=on_move)
listener.start()

# Continuously print the scaled speed
while True:
    speed = calculate_scaled_speed()
    print(f"Scaled Mouse Speed: {speed}/5")
    time.sleep(0.1)  # Update every 100ms