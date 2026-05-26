"""Bridge between the API and the standalone tongue-analysis predictor.

`tongue.predict_result_from_bytes.generate_predict_result_json_from_bytes`
returns a JSON string whose user-facing strings are concatenated bilingual
text (e.g. ``"白苔舌White coating tongue"``). This module:

  1. Runs that predictor.
  2. Parses its JSON.
  3. Splits each concatenated string into ``{zh, en}``.
  4. Maps the result into our typed ``TongueAnalysis`` model.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .models import (
    BilingualText,
    TongueAnalysis,
    TongueDetectedLabel,
    TongueDetection,
    TongueHealthRisk,
)

# Position of the first Latin letter in a "zh+en" concatenated string —
# everything before is Chinese (incl. any zh punctuation), everything from
# that index onwards is English.
_LATIN_LETTER = re.compile(r"[A-Za-z]")


def split_zh_en(text: str | None) -> BilingualText:
    """Split a concatenated zh+en string into {zh, en}.

    Examples
    --------
    >>> split_zh_en("白苔舌White coating tongue")
    BilingualText(zh='白苔舌', en='White coating tongue')

    >>> split_zh_en("舌苔偏白，常作为……。A white coating on the tongue…")
    BilingualText(zh='舌苔偏白，常作为……。', en='A white coating on the tongue…')
    """
    if not text:
        return BilingualText(zh="", en="")
    match = _LATIN_LETTER.search(text)
    if not match:
        return BilingualText(zh=text.strip(), en="")
    idx = match.start()
    return BilingualText(zh=text[:idx].strip(), en=text[idx:].strip())


def tongue_analysis_from_json(result_str: str) -> TongueAnalysis:
    """Parse the predictor's JSON string into a typed ``TongueAnalysis``.

    Raises ``ValueError`` if the JSON is malformed or missing required
    structure; the caller decides whether to fall back to a mock.
    """
    payload: Any = json.loads(result_str)
    if not isinstance(payload, dict):
        raise ValueError("predictor JSON root must be an object")

    raw_labels = payload.get("detected_labels", {}) or {}
    detected_labels = [
        TongueDetectedLabel(name=split_zh_en(name), count=int(count))
        for name, count in raw_labels.items()
    ]

    raw_risks = payload.get("possible_disease_or_health_risks", []) or []
    risks = [
        TongueHealthRisk(
            risk=split_zh_en(item.get("risk")),
            score=float(item.get("score", 0.0)),
        )
        for item in raw_risks
        if isinstance(item, dict)
    ]

    raw_detections = payload.get("detections", []) or []
    detections = []
    for det in raw_detections:
        if not isinstance(det, dict):
            continue
        detections.append(
            TongueDetection(
                class_id=int(det.get("class_id", -1)),
                label=str(det.get("label", "")),
                name=split_zh_en(det.get("name")),
                confidence=float(det.get("confidence", 0.0)),
                meaning=split_zh_en(det.get("meaning")),
                possible_risks=[split_zh_en(r) for r in det.get("possible_risks", []) or []],
            )
        )

    return TongueAnalysis(
        detected_labels=detected_labels,
        possible_disease_or_health_risks=risks,
        detections=detections,
    )
