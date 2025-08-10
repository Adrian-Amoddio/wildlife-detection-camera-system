# EC2 Server Backend

This folder contains all scripts and code for the EC2 instance used in the Wildlife Detection Camera System. It includes two main components:

- app.py - Flask server to receive and serve sensor data.
- NGINX RTMP Server - Used to relay live HLS video streams from the Raspberry Pi.

## Folder Structure

```
ec2-server/
├── environmental_sensor/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── nginx-rtmp/
│   ├── nginx.conf          # RTMP and HLS server config for NGINX
│   ├── docker-compose.yml
│   └── nginx-hls/
```

## Deployment Notes

- The **NGINX container** exposes ports `80` and `1935`. It mounts:

  - `nginx.conf` to `/etc/nginx/nginx.conf`
  - `nginx-hls/` to `/opt/data/hls`

- The **Flask environmental sensor API** runs on port `5000` by default and supports:
  - `POST /sensor` — Accepts sensor readings as JSON.
  - `GET /sensor` — Returns latest received sensor data.

## Prerequisites

- EC2 instance running Ubuntu (or similar Linux)
- Docker + Docker Compose installed
- Open ports:
  - **1935** for RTMP ingest from the Pi
  - **80** for HLS playback to the frontend

## Setup

To run the NGINX container:

```bash
cd nginx-rtmp/
sudo docker-compose up -d
```

To build and run the Flask relay (optional if containerized):

```bash
cd environmental_sensor/
pip install -r requirements.txt
python app.py
```
