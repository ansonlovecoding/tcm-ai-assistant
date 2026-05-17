from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, conint, confloat

Gender = Literal["male", "female", "other"]


class PatientInfo(BaseModel):
    age: conint(ge=0, le=150)
    gender: Gender
    height: confloat(gt=30, lt=260)  # cm
    weight: confloat(gt=2, lt=400)   # kg


class SessionCreated(BaseModel):
    session_id: str
    patient: PatientInfo
    created_at: datetime


class BilingualText(BaseModel):
    zh: str
    en: str


class TongueAnalysis(BaseModel):
    body_color: BilingualText
    coating: BilingualText
    shape: BilingualText
    notes: BilingualText


class TongueResult(BaseModel):
    session_id: str
    image_id: str
    received_bytes: int
    analysis: TongueAnalysis


class PulseSample(BaseModel):
    """Submitted from the external pulse device."""

    duration_ms: conint(gt=0, le=120_000) = 30_000
    sample_rate_hz: conint(gt=0, le=2000) = 200
    # Optional: list of floats from the device; if absent, server mocks it.
    waveform: Optional[list[float]] = None


class PulseAnalysis(BaseModel):
    pulse_type: BilingualText
    rate_bpm: int
    rhythm: BilingualText
    strength: BilingualText
    notes: BilingualText


class PulseResult(BaseModel):
    session_id: str
    capture_id: str
    sample_count: int
    analysis: PulseAnalysis


class DiagnosisAdvice(BaseModel):
    lifestyle: BilingualText
    diet: BilingualText
    herbal_tea: BilingualText


class DiagnosisResult(BaseModel):
    session_id: str
    pattern: BilingualText
    summary: BilingualText
    advice: DiagnosisAdvice
    disclaimer: BilingualText
    generated_at: datetime
