import mss
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import time

# Configurable threshold for minimum screen percentage
MIN_COLOR_PERCENTAGE = 20  # Minimum percentage a color must occupy (change as needed)

def get_screen_colors(num_colors=5):
    # MIN_COLOR_PERCENTAGE
    with mss.mss() as sct:
        # Capture the screen
        screenshot = sct.grab(sct.monitors[1])  # Primary screen
        
        # Convert to PIL Image and resize for faster processing
        img = Image.fromarray(np.array(screenshot)).convert("RGB")
        img = img.resize((100, 100))  # Downscale for clustering efficiency

        # Convert to NumPy array and reshape
        pixels = np.array(img).reshape(-1, 3)

        # Use K-Means to find dominant colors
        kmeans = KMeans(n_clusters=num_colors, n_init=10)
        labels = kmeans.fit_predict(pixels)
        cluster_centers = kmeans.cluster_centers_.astype(int)

        # Count occurrences of each color
        unique, counts = np.unique(labels, return_counts=True)
        color_distribution = dict(zip(unique, counts))

        # Calculate percentage of each color
        total_pixels = pixels.shape[0]
        filtered_colors = [
            (tuple(cluster_centers[idx]), round((count / total_pixels) * 100, 2))
            for idx, count in color_distribution.items()
            if (count / total_pixels) * 100 >= MIN_COLOR_PERCENTAGE  # Only keep colors above threshold
        ]

        # Sort by highest percentage
        filtered_colors.sort(key=lambda x: x[1], reverse=True)

        return filtered_colors[:num_colors]  # Return up to 5 colors

# Stream dominant screen colors in real-time
print(" Streaming screen colors (RGB, % of screen)...")
while True:
    colors = get_screen_colors()
    print(f" Screen Colors: {colors}")
    time.sleep(0.5)  # Adjust refresh rate as needed