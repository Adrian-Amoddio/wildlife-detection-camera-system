# Raspberry Pi Backend

This folder contains the scripts and code for the Raspberry Pi 5 used in the Wildlife Detection Camera System. It handles camera control, motion detection, sending sensor data, and live video streaming.

## Folder Structure

```
pi/
├── capture_api.py               # Flask API
├── motion_trigger_picamera2.py  # Script for continuous motion detection and triggering the Canon R6
├── start_stream.sh               # Starts the video stream from the Pi
├── send_sensor_data.py           # Sends temperature, pressure and humidity data to EC2 server
├── requirements.txt
└── README.md
```

## Key Functions

- **capture_api.py** — Provides REST endpoints to control capture modes and take high-resolution photos.
- **motion_trigger_picamera2.py** — Runs motion detection and triggers the camera.
- **start_stream.sh** — Starts an HLS stream via `ffmpeg`.
- **send_sensor_data.py** — Reads sensor values and sends them to the EC2 backend.

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Start the capture API:

   ```bash
   python3 capture_api.py
   ```

3. (Optional) Start motion detection:

   ```bash
   python3 motion_trigger_picamera2.py
   ```

4. (Optional) Start live streaming:
   ```bash
   ./start_stream.sh
   ```

## Notes

- Works with Canon EOS R6 connected via USB and `gphoto2`.
- `.cr3` RAW images are automatically converted to `.jpg` for storage or upload.

## License

This project is licensed under the [MIT License](../LICENSE).
