# EC2 Server Backend

This folder contains all server-side code and configuration for the EC2 instance used in the **Wildlife Camera System**. It includes two main components:

- **Environmental Sensor Relay:** A lightweight Flask server to receive and serve sensor data.
- **NGINX RTMP Server:** Used to relay live HLS video streams from the Raspberry Pi.

## Folder Structure

```
ec2-server/
├── environmental_sensor/
│   ├── app.py              # Flask server for receiving and serving sensor data
│   ├── Dockerfile          # Container for sensor relay service
│   └── requirements.txt    # Python dependencies for Flask app
│
├── nginx-rtmp/
│   ├── nginx.conf          # RTMP + HLS server config for NGINX
│   ├── docker-compose.yml  # Optional Docker Compose setup
│   └── nginx-hls/          # HLS segment output directory (bind-mounted)
```

## Deployment Notes

- The **NGINX container** exposes ports `80` and `1935`. It mounts:
  - `nginx.conf` to `/etc/nginx/nginx.conf`
  - `nginx-hls/` to `/opt/data/hls`

- The **Flask relay app** runs on port `5000` by default and supports:
  - `POST /sensor` — Accepts sensor readings as JSON.
  - `GET /sensor` — Returns latest received sensor data.

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

---

For full integration and setup instructions, refer to the main project [README](../../README.md).