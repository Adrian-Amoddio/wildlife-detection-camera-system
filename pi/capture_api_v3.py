#!/usr/bin/env python3
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import subprocess
import os
import time
import signal
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict

# ----------------------------------------------#
from ultralytics import YOLO
import cv2
import numpy as np

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Directories and files
CAPTURE_DIR = "/home/pi5-01/captures"
MODE_FILE = "/tmp/current_mode"
MOTION_PID_FILE = "/tmp/motion_pid"
STREAM_PID_FILE = "/tmp/stream_pid"
STREAM_SCRIPT = "/home/pi5-01/start_stream.sh"
MOTION_SCRIPT = "/home/pi5-01/motion_trigger_picamera2.py"

# Where annotated previews are saved for the frontend
STATIC_DIR = "/home/pi5-01/static"
LATEST_JPG = os.path.join(CAPTURE_DIR, "latest.jpg")

os.makedirs(CAPTURE_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# --- EDIT ME: default labels to keep when clicking AI Detect ---
SERVER_LABEL_FILTER: List[str] = ["refrigerator", "dog", "bird"]

# YOLO model (lazy-loaded)
MODEL_PATH = "yolov8n.pt"
_yolo_model: Optional[YOLO] = None

latest_sensor_data = None

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def json_error(message: str, status: int = 500):
    return jsonify({"ok": False, "status": "error", "message": message}), status


def get_model() -> YOLO:
    global _yolo_model
    if _yolo_model is None:
        app.logger.info("Loading YOLO model: %s", MODEL_PATH)
        _yolo_model = YOLO(MODEL_PATH)
    return _yolo_model


def _camera_still_cmd() -> str:
    if shutil.which("rpicam-still"):
        return "rpicam-still"
    if shutil.which("libcamera-still"):
        return "libcamera-still"
    raise FileNotFoundError("No Pi camera CLI found (rpicam-still or libcamera-still)")


def _label_matches(label: str, label_filter: Optional[List[str]]) -> bool:
    if not label_filter:
        return True
    return any(label.lower() == f.lower() for f in label_filter)


def _draw_boxes(img: np.ndarray, detections: List[Dict]) -> np.ndarray:
    for det in detections:
        x1, y1, x2, y2 = map(int, det["bbox"])
        label = f"{det['label']} {det['conf']:.2f}"
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, label, (x1, max(y1 - 10, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return img


def _no_cache_send_file(filepath: str, mimetype: str):
    resp = send_file(filepath, mimetype=mimetype)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


def get_mode_string() -> str:
    if not os.path.exists(MODE_FILE):
        return "unknown"
    with open(MODE_FILE) as f:
        return f.read().strip() or "unknown"


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route("/capture", methods=["POST"])
def capture_photo():
    label_filter = request.json.get("labels") if request.is_json else SERVER_LABEL_FILTER
    tmp_jpg = os.path.join(CAPTURE_DIR, "tmp.jpg")
    out_path = os.path.join(STATIC_DIR, f"annotated_{int(time.time())}.jpg")

    try:
        # Capture image from Pi camera
        camera_cmd = _camera_still_cmd()
        subprocess.run([camera_cmd, "-o", tmp_jpg, "-t", "1000", "--nopreview"], check=True)

        model = get_model()
        names = model.names
        dets_kept = []
        annotated_rel = None

        # Run YOLO detection
        results = model(tmp_jpg)
        for r in results:
            for b in r.boxes:
                cls_id = int(b.cls[0])
                conf = float(b.conf[0])
                x1, y1, x2, y2 = map(float, b.xyxy[0])
                lab = names.get(cls_id, str(cls_id))
                if _label_matches(lab, label_filter):
                    dets_kept.append({
                        "label": lab,
                        "conf": round(conf, 3),
                        "bbox": [x1, y1, x2, y2]
                    })

            if len(dets_kept) > 0:
                img = cv2.imread(tmp_jpg)  # BGR
                img = _draw_boxes(img, dets_kept)
                cv2.imwrite(out_path, img)
                annotated_rel = f"/static/{os.path.basename(out_path)}"

        return jsonify({
            "ok": True,
            "count": len(dets_kept),
            "detections": dets_kept,
            "annotated_image": annotated_rel,
            "labels_used": (label_filter or "ALL")
        })

    except FileNotFoundError:
        logging.exception("Camera CLI not found")
        return json_error("Camera CLI not found. Install rpicam-apps (Bookworm) or libcamera.", 500)
    except subprocess.CalledProcessError as e:
        logging.exception("Pi camera capture failed")
        return json_error(f"Pi camera capture failed: {e}", 500)
    except Exception as e:
        logging.exception("YOLO detect failed")
        return json_error(f"YOLO detect failed: {e}", 500)
    finally:
        try:
            if os.path.exists(tmp_jpg):
                os.remove(tmp_jpg)
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Static + Health
# -----------------------------------------------------------------------------
@app.route('/static/<path:filename>', methods=['GET'])
def serve_static(filename):
    abs_path = os.path.join(STATIC_DIR, filename)
    if not os.path.isfile(abs_path):
        return json_error("File not found", 404)
    return _no_cache_send_file(abs_path, mimetype="image/jpeg")


@app.route('/health', methods=['GET'])
def health():
    cams = {
        "rpicam-still": bool(shutil.which("rpicam-still")),
        "libcamera-still": bool(shutil.which("libcamera-still"))
    }
    return jsonify({
        "ok": True,
        "mode": get_mode_string(),
        "camera_cli": cams,
        "model_loaded": _yolo_model is not None,
        "server_label_filter": SERVER_LABEL_FILTER,
    })


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
