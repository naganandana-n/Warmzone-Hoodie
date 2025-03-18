from pynput import mouse
import time
import numpy as np

# Store movement data
positions = []
timestamps = []
velocities = []  # Store speed changes (acceleration)
MAX_SPEED = 5000  # Adjust for sensitivity
HISTORY_SIZE = 100  # Use last 100 points for smoothing
DECAY_TIME = 200  # Time in seconds for speed to decay to 0
EMA_ALPHA = 0.1  # Smoothing factor for Exponential Moving Average (EMA) (Lower = slower response)
ACCELERATION_WEIGHT = 1.0  # Reduce acceleration influence (Prevent instant jumps)
ACCELERATION_LIMIT = 200  # Limit how much acceleration can boost speed
RAMP_UP_SPEED = 0.5  # Maximum allowed speed increase per update (prevents spikes)

# Track last computed speed
smoothed_speed = 0
last_update_time = time.time()

def on_move(x, y):
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
    """Calculate smoothed speed (0 to 5) considering acceleration & rapid small-area movements."""
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

    # **Apply gradual decay if no movement detected**
    time_since_last_move = time.time() - last_update_time
    if scaled_speed > 3:
        decay_factor = max(0, 1 - (time_since_last_move / (DECAY_TIME * 2)))  # Slower decay above 3
    elif scaled_speed > 2:
        decay_factor = max(0, 1 - (time_since_last_move / (DECAY_TIME * 1.5)))  # Medium decay
    else:
        decay_factor = max(0, 1 - (time_since_last_move / DECAY_TIME))  # Normal decay
    '''
    if time_since_last_move > 0.5:  # Start decay after 0.5 sec of inactivity
        decay_factor = max(0, 1 - (time_since_last_move / DECAY_TIME))
        smoothed_speed *= decay_factor  # Gradually decrease speed
    '''

    return round(smoothed_speed, 2)

# Start listening to mouse movement
listener = mouse.Listener(on_move=on_move)
listener.start()

# Continuously print the smoothed speed
while True:
    speed = calculate_scaled_speed()
    print(f"Smoothed Mouse Speed: {speed}/5")
    time.sleep(0.1)  # Update every 100ms