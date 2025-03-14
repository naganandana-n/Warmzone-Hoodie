import mss
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import time

def get_top_colors_per_quadrant(num_colors=1):
    """Captures the screen, divides it into 4 quadrants, and extracts the dominant color from each quadrant."""
    with mss.mss() as sct:
        # Capture the screen
        screenshot = sct.grab(sct.monitors[1])  # Monitor[1] is the primary screen
        
        # Convert to PIL Image and Ensure RGB Mode
        img = Image.fromarray(np.array(screenshot)).convert("RGB")

        # Get screen dimensions
        width, height = img.size

        # Define quadrants (split along x and y)
        quadrants = {
            "Top-Left": img.crop((0, 0, width//2, height//2)),
            "Top-Right": img.crop((width//2, 0, width, height//2)),
            "Bottom-Left": img.crop((0, height//2, width//2, height)),
            "Bottom-Right": img.crop((width//2, height//2, width, height))
        }

        dominant_colors = {}

        for quadrant, image in quadrants.items():
            # Resize for faster processing
            image = image.resize((50, 50))

            # Convert to NumPy array and reshape
            pixels = np.array(image).reshape(-1, 3)  # Ensures RGB format

            # Use K-Means to find the dominant color
            kmeans = KMeans(n_clusters=num_colors, n_init=10)
            kmeans.fit(pixels)

            # Get the dominant color
            dominant_colors[quadrant] = tuple(kmeans.cluster_centers_[0].astype(int))

        return dominant_colors

# Stream dominant colors from 4 quadrants in real-time
print("🎨 Streaming dominant colors from 4 screen quadrants...")
while True:
    colors = get_top_colors_per_quadrant()
    print(f"🔲 Quadrant Colors: {colors}")
    time.sleep(0.5)  # Adjust refresh rate as needed