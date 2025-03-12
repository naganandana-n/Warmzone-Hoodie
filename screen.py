import mss
import numpy as np
from PIL import Image
import time

def get_screen_color():
    """Captures the screen and extracts the dominant color"""
    with mss.mss() as sct:
        # Capture the screen
        screenshot = sct.grab(sct.monitors[1])  # Monitor[1] is the primary screen
        
        # Convert to numpy array
        img = np.array(screenshot)

        # Resize to speed up processing
        img = Image.fromarray(img).resize((50, 50))

        # Get the average color
        avg_color = np.array(img).mean(axis=(0, 1)).astype(int)

        return tuple(avg_color[:3])  # RGB

# Stream screen colors in real-time
print("Streaming screen colors (RGB)...")
while True:
    color = get_screen_color()
    print(f"Screen Color: RGB {color}")
    time.sleep(0.5)  # Adjust refresh rate as needed