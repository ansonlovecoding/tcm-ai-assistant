from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, conint, confloat

Gender = Literal["male", "female", "other"]


class PatientInfo(BaseModel):
    """Basic information collected in step 1 of the web flow."""

    age: conint(ge=0, le=150) = Field(..., description="Age in years.")
    gender: Gender = Field(..., description="One of `male`, `female`, `other`.")
    height: confloat(gt=30, lt=260) = Field(..., description="Height in centimetres.")
    weight: confloat(gt=2, lt=400) = Field(..., description="Weight in kilograms.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "age": 32,
                "gender": "female",
                "height": 165,
                "weight": 54,
            }
        }
    )


class SessionCreated(BaseModel):
    session_id: str = Field(..., description="Opaque, short-lived session identifier.")
    patient: PatientInfo
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "9bdee0b2aea1",
                "patient": {"age": 32, "gender": "female", "height": 165, "weight": 54},
                "created_at": "2026-05-17T19:12:41Z",
            }
        }
    )


class BilingualText(BaseModel):
    """A user-facing string returned in both Chinese and English."""

    zh: str
    en: str

    model_config = ConfigDict(
        json_schema_extra={"example": {"zh": "气阴两虚", "en": "Qi-Yin deficiency"}}
    )


class TongueDetectedLabel(BaseModel):
    """One distinct tongue feature found by the YOLO model, with its count."""

    name: BilingualText = Field(..., description="Class name (bilingual).")
    count: int = Field(..., description="How many times this label was detected in the image.")


class TongueHealthRisk(BaseModel):
    """An aggregated health-risk hint derived from the detected features."""

    risk: BilingualText = Field(..., description="Risk indicator name (bilingual).")
    score: float = Field(..., description="Aggregated score from the rule engine; higher = stronger signal.")


class TongueDetection(BaseModel):
    """A single bounding-box detection emitted by the YOLO model."""

    class_id: int = Field(..., description="Numeric class id from the YOLO model.")
    label: str = Field(..., description="Short slug label (e.g. 'baitaishe').")
    name: BilingualText = Field(..., description="Class name (bilingual).")
    confidence: float = Field(..., description="Detection confidence in [0, 1].")
    meaning: BilingualText = Field(..., description="Interpretation of this feature (bilingual).")
    possible_risks: list[BilingualText] = Field(
        default_factory=list,
        description="Risk indicators that this detection contributes to.",
    )


class TongueAnalysis(BaseModel):
    """Structured tongue-image analysis matching the model's JSON output."""

    detected_labels: list[TongueDetectedLabel] = Field(
        default_factory=list,
        description="All distinct tongue features detected, with counts.",
    )
    possible_disease_or_health_risks: list[TongueHealthRisk] = Field(
        default_factory=list,
        description="Health-risk indicators aggregated from the detections, ranked by score.",
    )
    detections: list[TongueDetection] = Field(
        default_factory=list,
        description="Raw per-instance detections.",
    )


class TongueResult(BaseModel):
    session_id: str
    image_id: str = Field(..., description="Server-assigned id for the uploaded image.")
    received_bytes: int
    analysis: TongueAnalysis

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "9bdee0b2aea1",
                "image_id": "75d5108ed0",
                "received_bytes": 184231,
                "analysis": {
                    "detected_labels": [
                        {"name": {"zh": "白苔舌", "en": "White coating tongue"}, "count": 1},
                        {"name": {"zh": "裂纹舌", "en": "Cracked tongue"},        "count": 1},
                        {"name": {"zh": "齿痕舌", "en": "Dentate tongue"},        "count": 2},
                    ],
                    "possible_disease_or_health_risks": [
                        {"risk": {"zh": "津液不足风险", "en": "Risk of Insufficient Body Fluids"},                  "score": 1.135},
                        {"risk": {"zh": "阴虚风险",     "en": "Risk of Yin Deficiency"},                          "score": 1.135},
                        {"risk": {"zh": "脾虚湿重风险", "en": "Risk of Spleen Deficiency and Excessive Dampness"}, "score": 1.124},
                        {"risk": {"zh": "寒湿风险",     "en": "Risk of Cold-Dampness"},                            "score": 0.864},
                        {"risk": {"zh": "脾胃功能偏弱风险", "en": "Risk of Weak Spleen Function"},                   "score": 0.864},
                    ],
                    "detections": [
                        {
                            "class_id": 9,
                            "label": "baitaishe",
                            "name": {"zh": "白苔舌", "en": "White coating tongue"},
                            "confidence": 0.8637,
                            "meaning": {
                                "zh": "舌苔偏白，常作为寒湿、脾胃功能偏弱或早期外感的观察信号。",
                                "en": "A white coating on the tongue is often seen as a sign of cold-dampness, weak spleen function, or early external contraction.",
                            },
                            "possible_risks": [
                                {"zh": "寒湿风险", "en": "Risk of Cold-Dampness"},
                                {"zh": "脾胃功能偏弱风险", "en": "Risk of Weak Spleen Function"},
                            ],
                        }
                    ],
                },
            }
        }
    )


class PulseSample(BaseModel):
    """Capture metadata submitted from the external pulse-diagnosis device."""
    waveform: list[float] = Field(
        None,
        description="pulse sample data, length should be more than 256",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"waveform": [1.29, 1.2]}
        }
    )

class PulseAnalysis(BaseModel):
    sbp: float = Field(..., description="SBP (Systolic Blood Pressure)")
    dbp: float = Field(..., description="DBP (Diastolic Blood Pressure)")


class PulseResult(BaseModel):
    session_id: str
    capture_id: str
    sample_count: int
    analysis: PulseAnalysis

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "9bdee0b2aea1",
                "capture_id": "785a38a8cf",
                "analysis": {
                    "sbp": 148.92,
                    "dbp": 61.52
                },
            }
        }
    )


class DiagnosisAdvice(BaseModel):
    lifestyle: BilingualText = Field(..., description="作息建议。")
    diet: BilingualText = Field(..., description="饮食建议。")
    herbal_tea: BilingualText = Field(..., description="代茶饮参考。")


class DiagnosisResult(BaseModel):
    session_id: str
    pattern: BilingualText = Field(..., description="证型 — the differentiated pattern.")
    summary: BilingualText
    advice: DiagnosisAdvice
    disclaimer: BilingualText
    generated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "9bdee0b2aea1",
                "pattern": {
                    "zh": "气阴两虚 · 肝郁脾虚",
                    "en": "Qi-Yin Deficiency with Liver Qi Stagnation and Spleen Deficiency",
                },
                "summary": {
                    "zh": "综合舌脉，提示气阴俱不足，肝气欠舒，脾运失健。",
                    "en": "Combined tongue and pulse findings suggest deficiency of both Qi and Yin, with constrained liver Qi and impaired spleen function.",
                },
                "advice": {
                    "lifestyle": {
                        "zh": "规律作息，每日 23 点前入睡。",
                        "en": "Keep a regular schedule, sleep before 11 PM.",
                    },
                    "diet": {
                        "zh": "清淡饮食，多食山药、莲子。",
                        "en": "Light diet; favour Chinese yam and lotus seed.",
                    },
                    "herbal_tea": {
                        "zh": "太子参 6 克 + 麦冬 6 克 + 陈皮 3 克。",
                        "en": "6g Tai Zi Shen + 6g Mai Dong + 3g Chen Pi.",
                    },
                },
                "disclaimer": {
                    "zh": "本报告由 AI 生成，仅供参考。",
                    "en": "AI-generated, for reference only.",
                },
                "generated_at": "2026-05-17T19:12:41Z",
            }
        }
    )
