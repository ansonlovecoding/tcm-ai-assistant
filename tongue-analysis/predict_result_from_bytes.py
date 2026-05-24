from pathlib import Path
import subprocess
import sys
import tempfile


BASE_DIR = Path(__file__).resolve().parent

PREDICT_SCRIPT = BASE_DIR / "coco" / "predict_tongue_disease.py"
MODEL_PATH = BASE_DIR / "runs" / "train-2" / "weights" / "best.pt"


def generate_predict_result_json_from_bytes(
    image_bytes: bytes,
    output_json_path: Path | str = "predict_result.json",
    conf: float = 0.25,
) -> None:
    """
    输入图片 bytes，调用 coco/predict_tongue_disease.py，
    直接生成 predict_result.json 文件。
    """
    output_json_path = Path(output_json_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        image_path = temp_dir / "input_image.jpg"

        image_path.write_bytes(image_bytes)

        command = [
            sys.executable,
            str(PREDICT_SCRIPT),
            "--model",
            str(MODEL_PATH),
            "--image",
            str(image_path),
            "--conf",
            str(conf),
            "--save-json",
            str(output_json_path),
        ]

        subprocess.run(command, check=True)