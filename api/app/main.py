"""FastAPI entry point for the TCM diagnosis API.

Interactive documentation is available at:

* `/docs`        — Swagger UI ("Try it out")
* `/redoc`       — ReDoc reference layout
* `/openapi.json` — raw OpenAPI 3.1 spec
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from . import mock_data
from .models import (
    DiagnosisResult,
    PatientInfo,
    PulseResult,
    PulseSample,
    SessionCreated,
    TongueResult, PulseAnalysis,
)
from .store import store
from .tongue_predictor import tongue_analysis_from_json
from pulse.mock_ppg import MockPpg
from pulse.predict import BloodPressurePredictor
from tongue.predict_result_from_bytes import generate_predict_result_json_from_bytes

# Number of consecutive PPG samples the CNN1D model expects (see pulse/train.py).
PULSE_WINDOW_SIZE = 256

API_DESCRIPTION = """
Mock backend powering the **Qi-Huang AI / 岐黄智诊** single-page web app.

The web flow is a four-step pipeline that maps directly onto these endpoints:

| Step | Action                       | Endpoint                              |
|------|------------------------------|---------------------------------------|
| 1    | Patient basic info           | `POST /api/sessions`                  |
| 2    | Upload tongue image          | `POST /api/sessions/{id}/tongue`      |
| 3    | Submit pulse capture         | `POST /api/sessions/{id}/pulse`       |
| 4    | Generate AI diagnosis        | `POST /api/sessions/{id}/diagnose`    |

All user-facing strings are returned bilingually as `{ "zh": "...", "en": "..." }`
so the frontend can pick the right locale without an extra round-trip.

> ⚠ **Disclaimer.** Output is AI-generated and intended for research and
> educational use only. It does **not** constitute medical advice.
"""

TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Liveness and readiness probes.",
    },
    {
        "name": "Sessions",
        "description": "Create and inspect a four-step diagnosis session.",
    },
    {
        "name": "Tongue",
        "description": "Step 2 — upload a tongue image and receive a (mock) analysis "
                       "of body colour, coating and shape.",
    },
    {
        "name": "Pulse",
        "description": "Step 3 — submit a pulse capture from the external device and "
                       "receive a (mock) pulse-type classification.",
    },
    {
        "name": "Diagnose",
        "description": "Step 4 — synthesise everything collected so far into a final "
                       "pattern-differentiation report.",
    },
]

app = FastAPI(
    title="TCM Diagnosis API",
    summary="Mock backend for the Qi-Huang AI / 岐黄智诊 SPA.",
    description=API_DESCRIPTION,
    version="0.1.0",
    contact={"name": "TCM Assistant"},
    license_info={"name": "For research and educational use only"},
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Convenience redirect to the Swagger UI."""
    return RedirectResponse(url="/docs")


@app.get(
    "/api/health",
    tags=["Health"],
    summary="Liveness check",
    response_description="Service status and current in-memory session count.",
)
def health() -> dict:
    """Return `{"status": "ok"}` plus the number of sessions held in memory."""
    return {"status": "ok", "sessions": len(store.all())}


@app.post(
    "/api/sessions",
    response_model=SessionCreated,
    status_code=201,
    tags=["Sessions"],
    summary="Create a diagnosis session",
    response_description="The new session id together with the echoed patient info.",
)
def create_session(patient: PatientInfo) -> SessionCreated:
    """Open a new diagnosis session for a patient (step 1 of the web flow)."""
    session = store.create(patient)
    return SessionCreated(
        session_id=session.id,
        patient=session.patient,
        created_at=session.created_at,
    )


@app.post(
    "/api/sessions/{session_id}/tongue",
    response_model=TongueResult,
    tags=["Tongue"],
    summary="Upload tongue image and analyse",
    response_description="Mock tongue analysis (body colour, coating, shape, notes).",
    responses={
        400: {"description": "Uploaded file is not an image."},
        404: {"description": "Session does not exist."},
    },
)
async def upload_tongue(session_id: str, image: UploadFile = File(...)) -> TongueResult:
    """Accept a single tongue image as multipart `image=@...` and return the analysis."""
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    if not (image.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="file must be an image")

    data = await image.read()
    image_id = uuid4().hex[:10]

    # Run the real YOLO tongue predictor and parse its JSON into our typed
    # TongueAnalysis. If anything goes wrong (predictor crash, malformed
    # JSON, weights missing, …) return None

    # analysis_source = "mock"
    # analysis = mock_data.mock_tongue_analysis(session_id, data)

    analysis = None
    analysis_source = "model"
    try:
        result_str = generate_predict_result_json_from_bytes(data)
        analysis = tongue_analysis_from_json(result_str)
    except Exception as exc:
        print(f"[upload_tongue] tongue predictor failed: {exc}")
        return TongueResult(
            session_id=session_id,
            image_id=image_id,
            received_bytes=len(data),
            analysis=analysis,
        )

    print(
        f"[upload_tongue] {session_id=} {image_id=} bytes={len(data)} source={analysis_source} "
        f"detections={len(analysis.detections)} risks={len(analysis.possible_disease_or_health_risks)}"
    )

    session.tongue_image_id = image_id
    session.tongue_image_bytes = len(data)
    session.tongue_analysis = analysis

    return TongueResult(
        session_id=session_id,
        image_id=image_id,
        received_bytes=len(data),
        analysis=analysis,
    )


@app.post(
    "/api/sessions/{session_id}/pulse",
    response_model=PulseResult,
    tags=["Pulse"],
    summary="Submit a pulse capture and analyse",
    response_description="Mock pulse analysis (type, rate, rhythm, strength, notes).",
    responses={404: {"description": "Session does not exist."}},
)
def submit_pulse(session_id: str, sample: PulseSample) -> PulseResult:
    """Accept a pulse capture from the external device and return the analysis."""
    try:
        session = store.get(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="session not found")

    # Real PPG window from the web (via the serial-connected pulse sensor),
    # or fall back to the simulated waveform when the device is unavailable
    # (e.g. browser without Web Serial, dev machine without the sensor).
    if sample.waveform and len(sample.waveform) >= PULSE_WINDOW_SIZE:
        waveform = sample.waveform[:PULSE_WINDOW_SIZE]
        waveform_source = "device"
    else:
        waveform = MockPpg().ppg
        waveform_source = "mock"

    capture_id = uuid4().hex[:10]
    print(f"[submit_pulse] {session_id=} {capture_id=} samples={len(waveform)} source={waveform_source}")

    predictor = BloodPressurePredictor()
    sbp, dbp = predictor.predict(waveform)
    analysis = PulseAnalysis(sbp=sbp, dbp=dbp)
    print(f"Predicted SBP: {sbp:.2f}")
    print(f"Predicted DBP: {dbp:.2f}")

    session.pulse_capture_id = capture_id
    session.pulse_sample_count = len(waveform)
    session.pulse_analysis = analysis

    return PulseResult(
        session_id=session_id,
        capture_id=capture_id,
        sample_count=len(waveform),
        analysis=analysis,
    )


@app.post(
    "/api/sessions/{session_id}/diagnose",
    response_model=DiagnosisResult,
    tags=["Diagnose"],
    summary="Generate the AI pattern report",
    response_description="Pattern, summary, lifestyle/diet/tea advice, and disclaimer.",
    responses={404: {"description": "Session does not exist."}},
)
def diagnose(session_id: str) -> DiagnosisResult:
    """Synthesise patient + tongue + pulse data into a final pattern report."""
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


@app.get(
    "/api/sessions/{session_id}",
    tags=["Sessions"],
    summary="Inspect a session",
    response_description="The full session state, including any analyses stored so far.",
    responses={404: {"description": "Session does not exist."}},
)
def get_session(session_id: str) -> dict:
    """Read everything the server currently knows about a session."""
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
