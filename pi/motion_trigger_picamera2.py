import time
import requests
import numpy as np
import cv2
from picamera2 import Picamera2

MIN_MOTION_AREA = 5000
COOLDOWN_SECONDS = 10

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(
    main={"format": "RGB888", "size": (640, 480)}))
picam2.start()

time.sleep(2)  # Allow for camera startup time


last_trigger_time = 0
prev_frame = picam2.capture_array()
prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_RGB2GRAY)
# Blur frames to reduce noise
prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

# Main loop for motion detection
while True:
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Calculate frame delta and determine if motion detected
    frame_delta = cv2.absdiff(prev_gray, gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if contour is large enough to count as motion
    motion_detected = any(cv2.contourArea(contour) >
                          MIN_MOTION_AREA for contour in contours)

    if motion_detected:
        now = time.time()
        if now - last_trigger_time > COOLDOWN_SECONDS:
            # print("Motion detected. Triggering R6...")
            try:
                r = requests.post("http://localhost:5001/capture", timeout=10)
                # print(f"Response: {r.status_code} {r.text}")
                last_trigger_time = now
            except requests.RequestException as e:
                print(f"Failed to trigger capture: {e}")
        else:
            # print("Motion detected, in cooldown.")
            pass

    prev_gray = gray
