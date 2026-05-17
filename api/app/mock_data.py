"""Deterministic-ish mock TCM analyses. Replace with real models later."""

from __future__ import annotations

import hashlib
import random
from typing import Optional

from .models import (
    BilingualText,
    DiagnosisAdvice,
    DiagnosisResult,
    PatientInfo,
    PulseAnalysis,
    TongueAnalysis,
)


TONGUE_VARIANTS: list[TongueAnalysis] = [
    TongueAnalysis(
        body_color=BilingualText(zh="淡红舌", en="Pale red body"),
        coating=BilingualText(zh="薄白苔", en="Thin white coating"),
        shape=BilingualText(zh="舌体适中，边缘略齿痕", en="Moderate size, slight teeth marks on edges"),
        notes=BilingualText(
            zh="提示气虚倾向，脾胃功能略弱。",
            en="Suggests mild Qi deficiency and a slightly weak spleen-stomach.",
        ),
    ),
    TongueAnalysis(
        body_color=BilingualText(zh="红舌", en="Red body"),
        coating=BilingualText(zh="黄薄苔", en="Thin yellow coating"),
        shape=BilingualText(zh="舌体偏瘦，舌尖红点", en="Slightly thin body, red spots on tip"),
        notes=BilingualText(
            zh="提示阴虚内热，情志或睡眠欠佳。",
            en="Suggests Yin deficiency with internal heat, possibly poor sleep or emotional strain.",
        ),
    ),
    TongueAnalysis(
        body_color=BilingualText(zh="淡白舌", en="Pale body"),
        coating=BilingualText(zh="白腻苔", en="White greasy coating"),
        shape=BilingualText(zh="舌体胖大", en="Enlarged body"),
        notes=BilingualText(
            zh="提示阳虚痰湿，代谢偏弱。",
            en="Suggests Yang deficiency with damp-phlegm and sluggish metabolism.",
        ),
    ),
]

PULSE_VARIANTS: list[PulseAnalysis] = [
    PulseAnalysis(
        pulse_type=BilingualText(zh="弦细脉", en="Wiry and thin pulse"),
        rate_bpm=78,
        rhythm=BilingualText(zh="节律规整", en="Regular rhythm"),
        strength=BilingualText(zh="中等偏弱", en="Moderately weak"),
        notes=BilingualText(
            zh="多见于肝郁、阴血不足。",
            en="Often seen in liver Qi stagnation with Yin/blood deficiency.",
        ),
    ),
    PulseAnalysis(
        pulse_type=BilingualText(zh="沉缓脉", en="Deep and slow pulse"),
        rate_bpm=64,
        rhythm=BilingualText(zh="节律规整", en="Regular rhythm"),
        strength=BilingualText(zh="较弱", en="Weak"),
        notes=BilingualText(
            zh="多见于阳虚、寒湿内停。",
            en="Often seen in Yang deficiency with internal cold-damp.",
        ),
    ),
    PulseAnalysis(
        pulse_type=BilingualText(zh="滑数脉", en="Slippery and rapid pulse"),
        rate_bpm=92,
        rhythm=BilingualText(zh="节律规整", en="Regular rhythm"),
        strength=BilingualText(zh="有力", en="Strong"),
        notes=BilingualText(
            zh="多见于痰热、湿热内蕴。",
            en="Often seen in phlegm-heat or damp-heat patterns.",
        ),
    ),
]

PATTERN_LIBRARY: list[tuple[BilingualText, BilingualText, DiagnosisAdvice]] = [
    (
        BilingualText(zh="气阴两虚 · 肝郁脾虚", en="Qi-Yin Deficiency with Liver Qi Stagnation and Spleen Deficiency"),
        BilingualText(
            zh="综合舌脉，提示气阴俱不足，肝气欠舒，脾运失健。",
            en="Combined tongue and pulse findings suggest deficiency of both Qi and Yin, with constrained liver Qi and impaired spleen function.",
        ),
        DiagnosisAdvice(
            lifestyle=BilingualText(
                zh="规律作息，每日 23 点前入睡；保持情绪舒畅，避免过劳。",
                en="Keep a regular schedule, sleep before 11 PM; maintain emotional ease and avoid overwork.",
            ),
            diet=BilingualText(
                zh="清淡饮食，少辛辣油腻；多食山药、莲子、百合、银耳。",
                en="Light diet — limit spicy and greasy foods. Favor Chinese yam, lotus seed, lily bulb, and white fungus.",
            ),
            herbal_tea=BilingualText(
                zh="代茶饮参考：太子参 6 克 + 麦冬 6 克 + 陈皮 3 克。",
                en="Reference tea: 6g Tai Zi Shen + 6g Mai Dong + 3g Chen Pi.",
            ),
        ),
    ),
    (
        BilingualText(zh="脾阳不振 · 痰湿内停", en="Spleen Yang Insufficiency with Internal Phlegm-Damp"),
        BilingualText(
            zh="舌脉提示阳气不足，痰湿内停，可见疲乏、身重、便溏等。",
            en="Findings indicate Yang deficiency with internal phlegm-damp, presenting fatigue, heaviness, and loose stools.",
        ),
        DiagnosisAdvice(
            lifestyle=BilingualText(
                zh="注意保暖，适度有氧运动，避免久坐贪凉。",
                en="Stay warm, take regular aerobic exercise, avoid prolonged sitting and cold exposure.",
            ),
            diet=BilingualText(
                zh="温食为主，少甜腻冷饮；推荐生姜红枣茶、薏苡仁粥。",
                en="Favor warm foods; reduce sweets and cold drinks. Try ginger-jujube tea and Job's-tears congee.",
            ),
            herbal_tea=BilingualText(
                zh="代茶饮参考：干姜 3 克 + 陈皮 3 克 + 红枣 2 枚。",
                en="Reference tea: 3g Gan Jiang + 3g Chen Pi + 2 jujubes.",
            ),
        ),
    ),
    (
        BilingualText(zh="肝胆湿热", en="Liver-Gallbladder Damp-Heat"),
        BilingualText(
            zh="舌脉提示湿热内蕴肝胆，可见口苦、烦躁、胁胀。",
            en="Findings indicate damp-heat in the liver and gallbladder, with possible bitter taste, irritability, and rib-side distension.",
        ),
        DiagnosisAdvice(
            lifestyle=BilingualText(
                zh="忌烟酒、熬夜；舒缓情绪，避免暴怒。",
                en="Avoid alcohol, smoking, and late nights; manage emotions and avoid outbursts.",
            ),
            diet=BilingualText(
                zh="清热利湿，少辛辣油炸；推荐冬瓜、绿豆、薏苡仁。",
                en="Clear heat and resolve damp; reduce spicy/fried foods. Favor winter melon, mung bean, Job's tears.",
            ),
            herbal_tea=BilingualText(
                zh="代茶饮参考：菊花 5 克 + 决明子 6 克 + 山楂 3 克。",
                en="Reference tea: 5g Ju Hua + 6g Jue Ming Zi + 3g Shan Zha.",
            ),
        ),
    ),
]


def _pick(seed: str, choices: list):
    digest = hashlib.md5(seed.encode()).digest()
    return choices[digest[0] % len(choices)]


def mock_tongue_analysis(session_id: str, image_bytes: bytes) -> TongueAnalysis:
    seed = f"tongue:{session_id}:{len(image_bytes)}"
    return _pick(seed, TONGUE_VARIANTS)


def mock_pulse_analysis(session_id: str, capture_id: str, sample_count: int) -> PulseAnalysis:
    seed = f"pulse:{session_id}:{capture_id}:{sample_count}"
    return _pick(seed, PULSE_VARIANTS)


def mock_pulse_waveform(duration_ms: int, sample_rate_hz: int) -> list[float]:
    """Generate a plausible pulse-like waveform for the given duration."""
    import math

    total = max(1, int((duration_ms / 1000) * sample_rate_hz))
    samples: list[float] = []
    rng = random.Random(duration_ms * 1000 + sample_rate_hz)
    bpm = rng.randint(60, 90)
    period = 60 / bpm  # seconds per beat
    for i in range(total):
        t = i / sample_rate_hz
        phase = (t % period) / period
        # main systolic peak around 0.18, dicrotic notch around 0.45
        val = (
            math.exp(-((phase - 0.18) ** 2) / 0.004) * 1.0
            + math.exp(-((phase - 0.45) ** 2) / 0.01) * 0.35
            - 0.08
        )
        val += rng.gauss(0, 0.015)
        samples.append(round(val, 4))
    return samples


def mock_diagnosis(
    session_id: str,
    patient: PatientInfo,
    tongue: Optional[TongueAnalysis],
    pulse: Optional[PulseAnalysis],
) -> tuple[BilingualText, BilingualText, DiagnosisAdvice]:
    seed = (
        f"dx:{session_id}:{patient.age}:{patient.gender}:"
        f"{tongue and tongue.body_color.en}:{pulse and pulse.pulse_type.en}"
    )
    return _pick(seed, PATTERN_LIBRARY)


def disclaimer() -> BilingualText:
    return BilingualText(
        zh="本报告由 AI 生成，仅供学习与参考，不构成医疗诊断。请咨询执业中医师。",
        en="This report is AI-generated for reference only and does not constitute medical diagnosis. Please consult a licensed TCM practitioner.",
    )


def make_diagnosis_result(
    session_id: str,
    patient: PatientInfo,
    tongue: Optional[TongueAnalysis],
    pulse: Optional[PulseAnalysis],
) -> DiagnosisResult:
    from datetime import datetime

    pattern, summary, advice = mock_diagnosis(session_id, patient, tongue, pulse)
    return DiagnosisResult(
        session_id=session_id,
        pattern=pattern,
        summary=summary,
        advice=advice,
        disclaimer=disclaimer(),
        generated_at=datetime.utcnow(),
    )
