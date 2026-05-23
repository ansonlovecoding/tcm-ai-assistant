from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a YOLO model for tongue coating detection.")
    parser.add_argument("--data", required=True, type=Path, help="Path to xxx.yaml")
    parser.add_argument("--model", default="yolo11n.pt", help="Base YOLO model, for example yolo11n.pt or yolov8n.pt.")
    parser.add_argument("--epochs", default=80, type=int)
    parser.add_argument("--imgsz", default=640, type=int)
    parser.add_argument("--batch", default=16, type=int)
    parser.add_argument("--device", default=None, help="Use 0 for GPU, cpu for CPU, or leave empty for auto.")
    parser.add_argument("--project", default="runs/tongue_coating")
    parser.add_argument("--name", default="train")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(args.model)
    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=20,
        pretrained=True,
        plots=True,
    )


if __name__ == "__main__":
    main()
