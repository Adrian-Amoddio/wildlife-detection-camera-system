#!/usr/bin/env python3


import argparse
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run YOLOv8 inference on an image/video or a folder of images (CPU-only)."
    )
    parser.add_argument(
        "--source", type=str, required=True,
        help="Path to an image/video file or a directory of images"
    )
    parser.add_argument(
        "--model", type=str, default="yolov8n.pt",
        help="YOLOv8 model (e.g. yolov8n.pt, yolov8s.pt, or custom.pt)"
    )
    parser.add_argument(
        "--conf", type=float, default=0.25,
        help="Confidence threshold (0–1)"
    )
    parser.add_argument(
        "--imgsz", type=int, default=640,
        help="Inference image size (pixels)"
    )
    parser.add_argument(
        "--project", type=str, default="runs/detect",
        help="Root output directory"
    )
    parser.add_argument(
        "--name", type=str, default="pi_demo",
        help="Run name (subfolder of project)"
    )
    parser.add_argument(
        "--save_txt", action="store_true",
        help="Also save YOLO-format labels"
    )
    parser.add_argument(
        "--save_crop", action="store_true",
        help="Also save cropped detections"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        from ultralytics import YOLO  # type: ignore
    except Exception:
        print(
            "ERROR: 'ultralytics' not installed. Try:\n"
            "  pip install --upgrade pip\n"
            "  pip install ultralytics opencv-python\n"
            "On Raspberry Pi OS, if OpenCV wheel fails:\n"
            "  pip install ultralytics\n"
            "  sudo apt-get update && sudo apt-get install -y python3-opencv",
            file=sys.stderr,
        )
        raise

    src = Path(args.source)
    if not src.exists():
        print(f"ERROR: source not found: {src}", file=sys.stderr)
        sys.exit(1)

    # Lightest default for Pi; force CPU for reliability.
    model = YOLO(args.model)
    device = "cpu"

    predict_kwargs = dict(
        source=str(src),
        conf=args.conf,
        imgsz=args.imgsz,
        device=device,
        project=args.project,
        name=args.name,
        save=True,
        save_txt=args.save_txt,
        save_crop=args.save_crop,
        exist_ok=True,
        verbose=True,
    )

    t0 = time.time()
    results = model.predict(**predict_kwargs)
    dt = time.time() - t0

    out_dir = Path(args.project) / args.name
    print("\n=== Inference complete ===")
    print(f"Input:   {src.resolve()}")
    print(f"Outputs: {out_dir.resolve()}")
    try:
        total = sum(len(r.boxes) for r in results)
        print(f"Detections: {total}  |  Elapsed: {dt:.2f}s")
    except Exception:
        print(f"Elapsed: {dt:.2f}s")


if __name__ == "__main__":
    main()
