# server/app.py
# Raspberry Pi (Bookworm) + Camera Module 3 (Wide)
# Single-shot AI detection triggered by the frontend:
# React -> POST /ai/detect -> Pi grabs a frame (libcamera-still) -> YOLOv8 -> JSON + annotated image

from flask import Flask, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import os, time, subprocess, cv2

app = Flask(__name__)
CORS(app)

# Store previews here so the React app can show the latest annotated result
os.makedirs("static", exist_ok=True)

# Light model for Pi; replace with your custom weights if you have them
MODEL_PATH = "yolov8n.pt"
model = YOLO(MODEL_PATH)  # ultralytics will auto-download on first run

def capture_frame_jpeg(out_path: str):
    """
    Uses Raspberry Pi's libcamera stack to capture a single JPEG.
    The --autofocus-on-capture flag works with Camera Module 3 (AF).
    Adjust width/height as desired. 1920x1080 keeps it snappy.
    """
    cmd = [
        "libcamera-still", "-n",
        "--width", "1920", "--height", "1080",
        "--autofocus-on-capture",
        "-o", out_path
    ]
    subprocess.run(cmd, check=True)

@app.get("/ai/health")
def health():
    return "ok"

@app.post("/ai/detect")
def detect():
    ts = int(time.time())
    raw_path = f"/tmp/cap_{ts}.jpg"
    out_path = f"static/detect_{ts}.jpg"

    # 1) Capture one frame from the Pi camera
    capture_frame_jpeg(raw_path)

    # 2) Run YOLOv8 once (single-shot)
    results = model.predict(source=raw_path, imgsz=640, conf=0.35, verbose=False)

    dets = []
    if results and len(results):
        r = results[0]
        names = r.names
        if r.boxes is not None and len(r.boxes) > 0:
            for b in r.boxes:
                cls_id = int(b.cls[0]); conf = float(b.conf[0])
                x1, y1, x2, y2 = map(lambda x: float(x), b.xyxy[0])
                dets.append({
                    "label": names.get(cls_id, str(cls_id)),
                    "conf": round(conf, 3),
                    "bbox": [x1, y1, x2, y2]
                })

        # 3) Save an annotated preview image the frontend can display
        annotated_rgb = r.plot()  # RGB numpy array with boxes drawn
        cv2.imwrite(out_path, cv2.cvtColor(annotated_rgb, cv2.COLOR_RGB2BGR))
    else:
        out_path = None

    return jsonify({
        "count": len(dets),
        "detections": dets,
        "annotated_image": f"/{out_path}" if out_path else None
    })

if __name__ == "__main__":
    # Bind to 0.0.0.0 so your React app can call it over LAN
    app.run(host="0.0.0.0", port=5001)
