from __future__ import annotations

import json
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import cv2
from fastapi import FastAPI, File, Form, UploadFile
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

DEFAULT_MODEL_PATH = (
    PROJECT_DIR
    / "runs"
    / "train-2"
    / "weights"
    / "best.pt"
)

DEFAULT_LABEL_CONFIG = BASE_DIR / "tongue_label_profiles.json"

DEFAULT_LABEL_PROFILE = {
    "cn": None,
    "meaning": "未配置类别含义。The category meaning is not configured.",
    "risks": ["未知风险Unknown risks"],
    "severity": 1,
}

app = FastAPI(title="Tongue Disease Prediction API")

model = YOLO(str(DEFAULT_MODEL_PATH))


def load_label_profiles(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Label profile config not found: {path}")

    profiles = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict):
        raise ValueError("Label profile config must be a JSON object.")

    return profiles


def risk_level(score: float) -> str:
    if score >= 8:
        return "high_attention"
    if score >= 4:
        return "attention"
    if score > 0:
        return "mild_attention"
    return "low"


def get_label_profile(label_profiles: dict, name: str) -> dict:
    profile = label_profiles.get(name)
    if profile is not None:
        return profile

    fallback = DEFAULT_LABEL_PROFILE.copy()
    fallback["cn"] = name
    return fallback


def predict_image(
    image_path: Path,
    conf: float = 0.25,
    label_config: Path = DEFAULT_LABEL_CONFIG,
    save_image_path: Path | None = None,
) -> dict:
    label_profiles = load_label_profiles(label_config)

    result = model.predict(str(image_path), conf=conf, verbose=False)[0]

    detections = []
    counts = Counter()
    risk_scores = defaultdict(float)
    total_score = 0.0

    for box in result.boxes:
        class_id = int(box.cls.item())
        confidence = float(box.conf.item())
        name = result.names.get(class_id, str(class_id))
        profile = get_label_profile(label_profiles, name)

        score = profile["severity"] * confidence
        total_score += score
        counts[profile["cn"]] += 1

        for risk in profile["risks"]:
            risk_scores[risk] += score

        detections.append(
            {
                "class_id": class_id,
                "label": name,
                "name": profile["cn"],
                "confidence": round(confidence, 4),
                "meaning": profile["meaning"],
                "possible_risks": profile["risks"],
            }
        )

    if not detections:
        summary = "未检测到可靠舌象目标，建议换一张清晰、光线均匀、舌头完整露出的图片。No reliable tongue image was detected. We recommend replacing it with a clearer image that shows the tongue fully exposed, with even lighting."
    elif total_score == 0:
        summary = "主要检测到健康舌信号，当前图像未显示明显异常舌象。The primary signal detected was a healthy tongue; the current image does not show any obvious abnormalities in the tongue."
    else:
        top_risks = sorted(risk_scores.items(), key=lambda item: item[1], reverse=True)[:5]
        summary = "检测到舌象异常信号，优先关注：Abnormal tongue signs detected, should be given priority attention:" + "、".join(
            risk for risk, _ in top_risks
        )

    if save_image_path:
        save_image_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(save_image_path), result.plot())

    return {
        "image": str(image_path),
        "model": str(DEFAULT_MODEL_PATH),
        "label_config": str(label_config),
        "confidence_threshold": conf,
        "medical_disclaimer": "本结果只适合作为学习、科研和健康风险提示，不能替代医生诊断。This result is only suitable as a reference for learning, research, and health risks, and cannot replace a doctor's diagnosis.",
        "risk_level": risk_level(total_score),
        "summary": summary,
        "detected_labels": dict(counts),
        "possible_disease_or_health_risks": [
            {"risk": risk, "score": round(score, 3)}
            for risk, score in sorted(risk_scores.items(), key=lambda item: item[1], reverse=True)
        ],
        "detections": detections,
    }


@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    conf: float = Form(0.25),
):
    suffix = Path(image.filename or "upload.jpg").suffix or ".jpg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await image.read())

    try:
        return predict_image(image_path=temp_path, conf=conf)
    finally:
        temp_path.unlink(missing_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}