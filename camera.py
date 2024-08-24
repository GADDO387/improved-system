from picamera2 import Picamera2, Preview
from datetime import datetime
import os

# Directory to store images
save_dir = "/home/pi/captured_images"
os.makedirs(save_dir, exist_ok=True)

# Initialize Picamera2
picam2 = Picamera2()

# Configure for still image capture
picam2.configure(picam2.create_still_configuration())

# Start the camera preview (optional, remove if not using a display)
picam2.start_preview(Preview.QTGL)

# Start the camera
picam2.start()

# Capture an image with a timestamp
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
image_path = os.path.join(save_dir, f"image_{current_time}.jpg")
picam2.capture_file(image_path)

print(f"Image saved at {image_path}")

# Stop the camera
picam2.stop()
