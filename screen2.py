import mss
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import time

def get_top_colors(num_colors=5):
    """Captures the screen and extracts the top dominant colors"""
    with mss.mss() as sct:
        # Capture the screen
        screenshot = sct.grab(sct.monitors[1])  # Monitor[1] is the primary screen
        
        # Convert to PIL Image and Ensure RGB Mode
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Resize for faster processing
        img = img.resize((100, 100))

        # Convert to NumPy array and reshape
        pixels = np.array(img).reshape(-1, 3)  # Ensures RGB format

        # Use K-Means to find the top colors
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        kmeans.fit(pixels)

        # Get the top colors
        dominant_colors = kmeans.cluster_centers_.astype(int)

        return [tuple(color) for color in dominant_colors]

# Stream the top 5 colors in real-time
print("Streaming top 5 screen colors (RGB)...")
while True:
    colors = get_top_colors()
    print(f"Top Colors: {colors}")
    time.sleep(0.5)  # Adjust refresh rate as needed