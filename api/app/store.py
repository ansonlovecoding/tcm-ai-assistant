"""In-memory session store. Replace with a real database later."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .models import (
    PatientInfo,
    PulseAnalysis,
    TongueAnalysis,
)


@dataclass
class Session:
    id: str
    patient: PatientInfo
    created_at: datetime
    tongue_image_id: Optional[str] = None
    tongue_image_bytes: int = 0
    tongue_analysis: Optional[TongueAnalysis] = None
    pulse_capture_id: Optional[str] = None
    pulse_sample_count: int = 0
    pulse_analysis: Optional[PulseAnalysis] = None
    history: list[str] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def create(self, patient: PatientInfo) -> Session:
        session = Session(
            id=uuid4().hex[:12],
            patient=patient,
            created_at=datetime.utcnow(),
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session

    def all(self) -> list[Session]:
        with self._lock:
            return list(self._sessions.values())


store = SessionStore()
