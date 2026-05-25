from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import yaml
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


def make_resolved_dataset_yaml(data_yaml: Path, project_root: Path) -> Path:
    with data_yaml.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    dataset_path = Path(data["path"])

    if not dataset_path.is_absolute():
        dataset_path = project_root / dataset_path

    data["path"] = str(dataset_path.resolve()).replace("\\", "/")

    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".yaml",
        delete=False,
        encoding="utf-8",
    )

    with temp_file:
        yaml.safe_dump(data, temp_file, allow_unicode=True, sort_keys=False)

    return Path(temp_file.name)


def main() -> None:
    args = parse_args()

    project_root = Path(__file__).resolve().parent

    data_path = args.data if args.data.is_absolute() else project_root / args.data
    data_path = data_path.resolve()

    project_path = Path(args.project)
    project_path = project_path if project_path.is_absolute() else project_root / project_path

    resolved_data_yaml = make_resolved_dataset_yaml(data_path, project_root)

    model = YOLO(args.model)
    model.train(
        data=str(resolved_data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=str(project_path),
        name=args.name,
        patience=20,
        pretrained=True,
        plots=True,
    )


if __name__ == "__main__":
    main()