import time
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()

# Define the location to save the image
image_path = "/var/www/html/images/plant_latest.jpg"

def capture_image():
    # Start the camera
    picam2.start_preview()

    # Give some time for the camera to adjust
    time.sleep(2)

    # Capture the image
    picam2.capture_file(image_path)

    # Stop the camera
    picam2.stop_preview()

# Capture the image every 10 minutes (adjust as needed)
while True:
    capture_image()
    time.sleep(600)  # Wait for 10 minutes
