from pathlib import Path
import subprocess
import sys
import tempfile


BASE_DIR = Path(__file__).resolve().parent

PREDICT_SCRIPT = BASE_DIR / "coco" / "predict_tongue_disease.py"
MODEL_PATH = BASE_DIR / "runs" / "train-2" / "weights" / "best.pt"


def generate_predict_result_json_from_bytes(image_bytes: bytes) -> str:
    """
    输入图片 bytes，调用 coco/predict_tongue_disease.py，
    返回 JSON 格式的字符串。

    临时图片和临时 predict_result.json 会在函数结束后自动删除。
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)

        image_path = temp_dir / "input_image.jpg"
        result_json_path = temp_dir / "predict_result.json"

        image_path.write_bytes(image_bytes)

        command = [
            sys.executable,
            str(PREDICT_SCRIPT),
            "--model",
            str(MODEL_PATH),
            "--image",
            str(image_path),
            "--save-json",
            str(result_json_path),
        ]

        subprocess.run(command, check=True)

        json_string = result_json_path.read_text(encoding="utf-8")

    return json_string