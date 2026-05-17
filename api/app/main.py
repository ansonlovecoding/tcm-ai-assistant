"""FastAPI entry point for the TCM diagnosis API."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import mock_data
from .models import (
    DiagnosisResult,
    PatientInfo,
    PulseResult,
    PulseSample,
    SessionCreated,
    TongueResult,
)
from .store import store

app = FastAPI(
    title="TCM Diagnosis API",
    description="Mock backend for the Qi-Huang AI / 岐黄智诊 single-page web app.",
    version="0.1.0",
)

# CORS is harmless even with the Vite proxy and lets the API be hit directly
# (e.g. from /docs or curl from another origin during testing).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "sessions": len(store.all())}


@app.post("/api/sessions", response_model=SessionCreated, status_code=201)
def create_session(patient: PatientInfo) -> SessionCreated:
    session = store.create(patient)
    return SessionCreated(
        session_id=session.id,
        patient=session.patient,
        created_at=session.created_at,
    )


@app.post("/api/sessions/{session_id}/tongue", response_model=TongueResult)
async def upload_tongue(session_id: str, image: UploadFile = File(...)) -> TongueResult:
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="file must be an image")

    data = await image.read()
    image_id = uuid4().hex[:10]
    analysis = mock_data.mock_tongue_analysis(session_id, data)

    session.tongue_image_id = image_id
    session.tongue_image_bytes = len(data)
    session.tongue_analysis = analysis

    return TongueResult(
        session_id=session_id,
        image_id=image_id,
        received_bytes=len(data),
        analysis=analysis,
    )


@app.post("/api/sessions/{session_id}/pulse", response_model=PulseResult)
def submit_pulse(session_id: str, sample: PulseSample) -> PulseResult:
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    waveform = sample.waveform or mock_data.mock_pulse_waveform(
        sample.duration_ms, sample.sample_rate_hz
    )
    capture_id = uuid4().hex[:10]
    analysis = mock_data.mock_pulse_analysis(session_id, capture_id, len(waveform))

    session.pulse_capture_id = capture_id
    session.pulse_sample_count = len(waveform)
    session.pulse_analysis = analysis

    return PulseResult(
        session_id=session_id,
        capture_id=capture_id,
        sample_count=len(waveform),
        analysis=analysis,
    )


@app.post("/api/sessions/{session_id}/diagnose", response_model=DiagnosisResult)
def diagnose(session_id: str) -> DiagnosisResult:
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    return mock_data.make_diagnosis_result(
        session_id=session.id,
        patient=session.patient,
        tongue=session.tongue_analysis,
        pulse=session.pulse_analysis,
    )


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")
    return {
        "session_id": session.id,
        "patient": session.patient.model_dump(),
        "created_at": session.created_at.isoformat(),
        "tongue": {
            "image_id": session.tongue_image_id,
            "received_bytes": session.tongue_image_bytes,
            "analysis": session.tongue_analysis.model_dump() if session.tongue_analysis else None,
        },
        "pulse": {
            "capture_id": session.pulse_capture_id,
            "sample_count": session.pulse_sample_count,
            "analysis": session.pulse_analysis.model_dump() if session.pulse_analysis else None,
        },
    }
