# Wildlife Camera System

End-to-end wildlife monitoring platform for remote, off-grid operation — designed to stream, detect motion, and capture high-resolution images from anywhere in the world.

A fully self-contained, solar-powered wildlife monitoring platform built from scratch. Streams live video, collects environmental data, and remotely triggers a Canon EOS R6 for high resolution stills.
Designed and implemented end-to-end using Raspberry Pi 5, Python/Flask, React, and AWS EC2, this project demonstrates skills in embedded systems, networking, API design, and modern web development.

Built end-to-end by me.

---

## 🎥 Demo

[![Watch the demo](https://img.youtube.com/vi/tZjDdPRHNxE/maxresdefault.jpg)](https://youtu.be/tZjDdPRHNxE)  
[▶ **Watch on YouTube**](https://youtu.be/tZjDdPRHNxE)

---

## Tech Stack

- **Hardware:** Raspberry Pi 5 (8GB), Pi Camera Module 3 Wide, Canon EOS R6 , PicoDev BMP280 sensor
- **Pi software:** Python 3.11, `libcamera`, `ffmpeg`, `gphoto2`
- **Backend (EC2):** NGINX RTMP/HLS, Flask (sensor data reciever)
- **Frontend:** React + Recharts (live stream, environmental telemetry, Canon R6 capture, mode toggling)
- **Protocols:** RTMP → HLS, REST (JSON), I²C (sensor)
- **Power and Enclosure:** LiFePO₄ battery, solar panel, custom lens port + weather-resistant case

---

## ![Build photo](docs/build-images/Deployed.JPG)

### Final UI Screenshots

![Final UI - Stream View](frontend/Final-UI-1.JPG)
![Final UI - Sensor Data](frontend/Final-UI-2.JPG)
![Final UI - Capture Function](frontend/Final-UI-3.JPG)

## ![Wiring Diagram](docs/Pi-Wildlife-Detection-System-Wiring-Diagram.JPG)

---

## What it does

- **Live stream**: Low-latency HLS stream from the Pi → EC2 → React front end
- **Motion detection**: Triggers the R6 for high-resolution stills (or you can capture manually).
- **Telemetry**: Temperature, pressure, humidity via BMP280 with charts where you can view the data.
- **Mode switching**: Toggle **Motion** ↔ **Streaming** from the dashboard.
- **Smart and Reliable UX**: Sensor polling, stream retry logic, and clear error states in the UI.

> **My role:** I designed and implemented the **entire system**—hardware choices, enclosure, Pi scripts, EC2 services, and the React frontend.

I am an engineer with a passion for embedded systems and photography. I wanted to make this project to demonstrate my skills and create something I can use for photography projects which can be used anywhere in the world to capture hard to reach places, scenes or wildlife. You can use the system to research behavioural and location analysis of wildlife and correlate that data against environmental parameters like: temperature, pressure and humidity. What's more you don't have to wait to retrieve the results you can access them instantly online and don't have to trek back into the wild to pickup any gear.

Future updates will include an advanced motion detection algorithm that can be remotely updated with a trained AI model to more specifically detect wildlife and events of interest.

---

## Project Structure

```
├── captures/                     # Optional saved test images or videos
│
├── docs/                          # Build images and final deployed photograph
│   ├── Pi-Wildlife-Detection-System-Wiring-Diagram.JPG
│   └── build-images/
│       ├── 1.jpg … 40.jpg
│       ├── AlFlange.JPG
│       └── Deployed.JPG
│
├── ec2-server/                    # Backend scripts and dockerfile for video stream and sensor data
│   ├── environmental_sensor/      # Flask API for sending BMP280 sensor data to the EC2 server
│   │   ├── app.py
│   │   ├── Dockerfile.txt
│   │   └── requirements.txt
│   │
│   └── nginx-rtmp/                 # RTMP/HLS server
│       ├── docker-compose.yml
│       ├── nginx.conf
│       └── nginx-hls/
│
├── frontend/                      # Front End React Website
│   └── react-frontend/
│       ├── player.html
│       ├── styles.css
│       └── pi-stream-ui/
│           ├── .env.example
│           ├── package.json
│           ├── public/
│           └── src/
│
├── hardware/                      # CAD/drawings for custom lens port for Canon R6
│   ├── acrylic-flange-files/
│   ├── aluminium-flange-files/
│   └── pmma-flange-files/
│
└── pi/                            # All scripts that run on the Pi for the different functions
    ├── capture_api.py              # Remote still photo capture with the Canon EOS R6
    ├── motion_trigger_picamera2.py # Motion detection script that triggers the R6
    ├── send_sensor_data.py         # Sends sensor data to the EC2 backend
    ├── start_stream.sh             # Used whenever the user switches into streaming mode
    └── requirements.txt
```

---

## Hardware

- Raspberry Pi 5 8GB
- Pi Camera Module 3 Wide
- Canon EOS R6 with 24–70mm f2.8 RF lens
- Picodev BMP280 environmental sensor
- D-Link Cat6 Mobile Hotspot
- Kings 12V LiFePO4 battery
- Kings 200W Solar Panel
- Kings Anderson Solar Extension Cable
- Dune MPPT Solar Charge Controller
- Tactix Black Extra Large Tough Case
- Custom camera lens port (see `/hardware/`)
- 2 × 6mm Waterproof cable glands

---

## Software

- Raspberry Pi OS (Bookworm or later, 64-bit)
- Python 3.11+
- `libcamera`
- `gphoto2`
- `ffmpeg`
- AWS EC2 backend (NGINX RTMP/HLS + Flask API)

---

## Installation

1. **Clone this repository** onto your Pi 5:

   ```bash
   git clone https://github.com/Adrian-Amoddio/wildlife-detection-camera-system.git
   cd wildlife-detection-camera-system/pi
   ```

2. **Install Python dependencies**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install system dependencies**:

   ```bash
   sudo apt update
   sudo apt install ffmpeg gphoto2 python3-pip libatlas-base-dev
   ```

4. **Configure environmental sensor**:

   - Ensure the BMP280 is connected via I²C
   - Enable I2C on the Pi:
     ```bash
     sudo raspi-config
     # Interfacing Options - I2C - Enable
     ```
   - Verify it’s detected:
     ```bash
     sudo apt install -y i2c-tools
     i2cdetect -y 1
     ```

5. **Set environment variables** (optional):
   - Create a `.env` file:
     ```bash
     SENSOR_API_URL=https://<ec2-server-ip>/sensor
     RTMP_SERVER_URL=rtmp://<ec2-server-ip>/live/stream
     ```

---

## Scripts Overview

- **capture_api.py** – Flask API to trigger still capture from the Canon EOS R6. Then return and save the image.
- **motion_trigger_picamera2.py** – Uses Pi Camera Module 3 Wide for motion detection to trigger R6 still capture or switch to streaming.
- **send_sensor_data.py** – Reads temperature, pressure, and humidity from BMP280 and sends JSON to EC2 backend every 10 seconds.
- **start_stream.sh** – Launches live streaming pipeline and sends to EC2 instance.

---

## Usage

### Start live stream

```bash
chmod +x start_stream.sh
./start_stream.sh
```

### Run environmental sensor loop

```bash
python3 send_sensor_data.py
```

### Run motion detection

```bash
python3 motion_trigger_picamera2.py
```

### Start capture API server

```bash
python3 capture_api.py
```

Trigger remote capture:

```bash
curl -X POST http://<pi-ip>:5000/capture
```

---

## Recommended Deployment

The scripts below need to be run on boot if you want the system to operate independantly. It is recommended you do this as running anything manually in remote areas is difficult.

- `capture_api.py`
- `send_sensor_data.py`

---

## Notes

- The motion detection and video screaming scripts cannot run simultanously. Only one can run at a time other wise this will cause an error or the pi will crash
- Canon EOS R6 must be powered on and connect with a USB to the Pi
- Ensure the EC2 instance is running before running any scripts on the pi or trying to access the front end.

---

## Setup References

- [Raspberry Pi scripts](pi/README.md)
- [EC2 backend](ec2-server/README.md)
- [Frontend UI](frontend/react-frontend/pi-stream-ui/README.md)

---

## License

MIT License — free to use, modify, and distribute.
