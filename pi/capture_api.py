from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import subprocess
import os
import time
import signal
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# Directories and files
CAPTURE_DIR = "/home/pi5-01/captures"
MODE_FILE = "/tmp/current_mode"
MOTION_PID_FILE = "/tmp/motion_pid"
STREAM_PID_FILE = "/tmp/stream_pid"
STREAM_SCRIPT = "/home/pi5-01/start_stream.sh"
MOTION_SCRIPT = "/home/pi5-01/motion_trigger_picamera2.py"
os.makedirs(CAPTURE_DIR, exist_ok=True)

latest_sensor_data = None

# Process killer functions


def kill_pid_file(pid_file):
    if not os.path.exists(pid_file):
        return
    try:
        with open(pid_file) as f:
            pid_txt = f.read().strip()
            pid = int(pid_txt) if pid_txt else -1
    except (ValueError, OSError):
        logging.warning("Bad PID file %s; removing.", pid_file)
        os.remove(pid_file)
        return

    try:
        os.killpg(pid, signal.SIGTERM)
        logging.info("Killed process group %s", pid)
    except ProcessLookupError:
        logging.warning("PID %s not running", pid)
    finally:
        try:
            os.remove(pid_file)
        except FileNotFoundError:
            pass


def kill_existing_camera_processes():
    kill_pid_file(STREAM_PID_FILE)
    kill_pid_file(MOTION_PID_FILE)

# Return the current mode of the system (streaming or motion detection)


def get_mode_string():
    if os.path.exists(MODE_FILE):
        with open(MODE_FILE) as f:
            mode = f.read().strip()
            if mode in ["motion", "stream"]:
                return mode
    return "unknown"


def set_mode_flag(mode):
    with open(MODE_FILE, "w") as f:
        f.write(mode)


def clear_mode_flag():
    try:
        os.remove(MODE_FILE)
    except FileNotFoundError:
        pass


# -----------------------------------------------------------------------------------------------------------
# Endpoints for mode switching

@app.route('/set-mode/<mode>', methods=['POST'])
def set_mode(mode):
    if mode not in ['motion', 'stream']:
        return jsonify({"status": "error", "message": "Invalid mode"}), 400

    current = get_mode_string()
    logging.info("Switching mode: %s -> %s", current, mode)

    kill_existing_camera_processes()
    clear_mode_flag()
    time.sleep(1.0)

    if mode == "motion":
        return start_motion()
    else:
        return start_stream()


@app.route('/toggle-mode', methods=['POST'])
def toggle_mode():
    mode = get_mode_string()
    return set_mode("stream" if mode == "motion" else "motion")


@app.route('/mode', methods=['GET'])
def get_mode():
    return jsonify({"mode": get_mode_string()})


def start_motion():
    logging.info("Starting motion detection...")
    try:
        motion_proc = subprocess.Popen(
            ["python3", MOTION_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
    except Exception as e:
        logging.exception("Failed to start motion detection")
        return jsonify({"status": "error", "message": str(e)}), 500

    with open(MOTION_PID_FILE, "w") as f:
        f.write(str(motion_proc.pid))
    set_mode_flag("motion")
    return jsonify({"status": "started", "mode": "motion"})

# Function to start the video stream.


def start_stream():
    logging.info("Starting video stream from shell script...")
    try:
        stream_proc = subprocess.Popen(
            ["bash", STREAM_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
    except Exception as e:
        logging.exception("Failed to start stream")
        return jsonify({"status": "error", "message": str(e)}), 500

    with open(STREAM_PID_FILE, "w") as f:
        f.write(str(stream_proc.pid))
    set_mode_flag("stream")
    return jsonify({"status": "started", "mode": "stream"})

# Image capture endpoint - Canon R6


@app.route('/capture', methods=['POST'])
def capture():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    cr3 = os.path.join(CAPTURE_DIR, f"capture_{timestamp}.cr3")
    jpg = os.path.join(CAPTURE_DIR, f"capture_{timestamp}.jpg")
    try:
        subprocess.run(
            ["gphoto2", "--capture-image-and-download", "--filename", cr3], check=True)
        subprocess.run(["darktable-cli", cr3, jpg], check=True)
        subprocess.run(
            ["rclone", "copy", jpg, "gdrive:RPiUploads"], check=True)
        return jsonify({"status": "success", "filename": jpg})
    except subprocess.CalledProcessError as e:
        logging.exception("Capture pipeline failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/latest-image', methods=['GET'])
def latest_image():
    jpg_files = sorted(
        [os.path.join(CAPTURE_DIR, f)
         for f in os.listdir(CAPTURE_DIR) if f.endswith(".jpg")],
        key=os.path.getmtime,
        reverse=True
    )
    if not jpg_files:
        return "No image found", 404
    return send_file(jpg_files[0], mimetype='image/jpeg')

# Sensor data endpoints


@app.route('/sensor', methods=['POST'])
def update_sensor():
    global latest_sensor_data
    latest_sensor_data = request.get_json(silent=True)
    logging.info("Received sensor data: %s", latest_sensor_data)
    return jsonify({"status": "ok"})


@app.route('/sensor/latest', methods=['GET'])
def get_latest_sensor():
    if latest_sensor_data is None:
        return jsonify({"status": "error", "message": "No data"}), 404
    return jsonify(latest_sensor_data)

# Optional GET alias so /sensor works in browsers too


@app.route('/sensor', methods=['GET'])
def get_latest_sensor_alias():
    return get_latest_sensor()


if __name__ == '__main__':
    # Frontend HTML used :5000 in some examples; this runs on :5001.
    app.run(host='0.0.0.0', port=5001)
