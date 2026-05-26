from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO


DEFAULT_LABEL_PROFILE = {
    "cn": None,
    "meaning": "未配置类别含义。The category meaning is not configured.",
    "risks": ["未知风险Unknown risks"],
    "severity": 1,
}


def load_label_profiles(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Label profile config not found: {path}")

    profiles = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict):
        raise ValueError("Label profile config must be a JSON object.")

    for label, profile in profiles.items():
        if not isinstance(profile, dict):
            raise ValueError(f"Profile for label '{label}' must be a JSON object.")

        for field in ("cn", "meaning", "risks", "severity"):
            if field not in profile:
                raise ValueError(f"Missing field '{field}' for label '{label}'.")

        if not isinstance(profile["risks"], list):
            raise ValueError(f"'risks' must be a list for label '{label}'.")

        if not isinstance(profile["severity"], (int, float)):
            raise ValueError(f"'severity' must be a number for label '{label}'.")

    return profiles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict tongue signals and health risks from an image.")
    parser.add_argument("--model", required=True, type=Path, help="Path to a trained YOLO best.pt model.")
    parser.add_argument("--image", required=True, type=Path, help="Input tongue image.")
    parser.add_argument("--conf", default=0.25, type=float, help="Confidence threshold.")
    parser.add_argument("--save-json", type=Path, help="Optional path for JSON output.")
    parser.add_argument("--save-image", type=Path, help="Optional path for annotated image.")
    parser.add_argument(
        "--label-config",
        default=Path(__file__).with_name("tongue_label_profiles.json"),
        type=Path,
        help="Path to tongue label profile JSON config.",
    )
    return parser.parse_args()


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


def main() -> None:
    args = parse_args()
    label_profiles = load_label_profiles(args.label_config)

    model = YOLO(str(args.model))
    result = model.predict(str(args.image), conf=args.conf, verbose=False)[0]

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

    output = {
        "image": str(args.image),
        "model": str(args.model),
        "label_config": str(args.label_config),
        "confidence_threshold": args.conf,
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

    print(json.dumps(output, indent=2, ensure_ascii=False))

    if args.save_json:
        args.save_json.parent.mkdir(parents=True, exist_ok=True)
        args.save_json.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.save_image:
        args.save_image.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(args.save_image), result.plot())


if __name__ == "__main__":
    main()