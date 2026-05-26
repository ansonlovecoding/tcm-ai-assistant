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
    TongueDetectedLabel,
    TongueDetection,
    TongueHealthRisk,
)


# Shorthand bilingual labels reused across mock variants — keeps each
# TongueAnalysis literal readable.
_LBL_BAITAI = BilingualText(zh="白苔舌", en="White coating tongue")
_LBL_LIEWEN = BilingualText(zh="裂纹舌", en="Cracked tongue")
_LBL_CHIHEN = BilingualText(zh="齿痕舌", en="Dentate tongue")
_LBL_HONGSHE = BilingualText(zh="红舌", en="Red tongue")
_LBL_HUANGTAI = BilingualText(zh="黄苔舌", en="Yellow coating tongue")
_LBL_PANGDA = BilingualText(zh="胖大舌", en="Enlarged tongue")

_RISK_FLUIDS = BilingualText(zh="津液不足风险", en="Risk of Insufficient Body Fluids")
_RISK_YIN = BilingualText(zh="阴虚风险", en="Risk of Yin Deficiency")
_RISK_DAMP_SPLEEN = BilingualText(zh="脾虚湿重风险", en="Risk of Spleen Deficiency and Excessive Dampness")
_RISK_COLD_DAMP = BilingualText(zh="寒湿风险", en="Risk of Cold-Dampness")
_RISK_WEAK_SPLEEN = BilingualText(zh="脾胃功能偏弱风险", en="Risk of Weak Spleen Function")
_RISK_HEAT = BilingualText(zh="内热风险", en="Risk of Internal Heat")
_RISK_PHLEGM = BilingualText(zh="痰湿风险", en="Risk of Phlegm-Dampness")


TONGUE_VARIANTS: list[TongueAnalysis] = [
    # Variant 1 — mirrors the example JSON the model emits (4 detections).
    TongueAnalysis(
        detected_labels=[
            TongueDetectedLabel(name=_LBL_BAITAI, count=1),
            TongueDetectedLabel(name=_LBL_LIEWEN, count=1),
            TongueDetectedLabel(name=_LBL_CHIHEN, count=2),
        ],
        possible_disease_or_health_risks=[
            TongueHealthRisk(risk=_RISK_FLUIDS,      score=1.135),
            TongueHealthRisk(risk=_RISK_YIN,         score=1.135),
            TongueHealthRisk(risk=_RISK_DAMP_SPLEEN, score=1.124),
            TongueHealthRisk(risk=_RISK_COLD_DAMP,   score=0.864),
            TongueHealthRisk(risk=_RISK_WEAK_SPLEEN, score=0.864),
        ],
        detections=[
            TongueDetection(
                class_id=9, label="baitaishe", name=_LBL_BAITAI, confidence=0.8637,
                meaning=BilingualText(
                    zh="舌苔偏白，常作为寒湿、脾胃功能偏弱或早期外感的观察信号。",
                    en="A white coating on the tongue is often seen as a sign of cold-dampness, weak spleen function, or early external contraction.",
                ),
                possible_risks=[_RISK_COLD_DAMP, _RISK_WEAK_SPLEEN],
            ),
            TongueDetection(
                class_id=7, label="liewenshe", name=_LBL_LIEWEN, confidence=0.5676,
                meaning=BilingualText(
                    zh="舌面裂纹明显，常作为津液不足、阴虚或长期消化吸收状态异常的观察信号。",
                    en="A cracked tongue is often seen as a sign of insufficient body fluids, yin deficiency, or abnormal digestive function.",
                ),
                possible_risks=[_RISK_FLUIDS, _RISK_YIN],
            ),
            TongueDetection(
                class_id=8, label="chihenshe", name=_LBL_CHIHEN, confidence=0.2964,
                meaning=BilingualText(
                    zh="舌边齿痕明显，常作为脾虚、湿重或水液代谢偏弱的观察信号。",
                    en="A dentate tongue is often seen as a sign of spleen deficiency, excessive dampness, or weak water metabolism.",
                ),
                possible_risks=[_RISK_DAMP_SPLEEN],
            ),
            TongueDetection(
                class_id=8, label="chihenshe", name=_LBL_CHIHEN, confidence=0.2654,
                meaning=BilingualText(
                    zh="舌边齿痕明显，常作为脾虚、湿重或水液代谢偏弱的观察信号。",
                    en="A dentate tongue is often seen as a sign of spleen deficiency, excessive dampness, or weak water metabolism.",
                ),
                possible_risks=[_RISK_DAMP_SPLEEN],
            ),
        ],
    ),
    # Variant 2 — Yin-deficiency-with-heat presentation.
    TongueAnalysis(
        detected_labels=[
            TongueDetectedLabel(name=_LBL_HONGSHE,   count=1),
            TongueDetectedLabel(name=_LBL_HUANGTAI,  count=1),
            TongueDetectedLabel(name=_LBL_LIEWEN,    count=1),
        ],
        possible_disease_or_health_risks=[
            TongueHealthRisk(risk=_RISK_HEAT,   score=1.420),
            TongueHealthRisk(risk=_RISK_YIN,    score=1.180),
            TongueHealthRisk(risk=_RISK_FLUIDS, score=0.910),
        ],
        detections=[
            TongueDetection(
                class_id=2, label="hongshe", name=_LBL_HONGSHE, confidence=0.7924,
                meaning=BilingualText(
                    zh="舌质偏红，常作为内热或阴虚的观察信号。",
                    en="A red tongue body is often seen as a sign of internal heat or yin deficiency.",
                ),
                possible_risks=[_RISK_HEAT, _RISK_YIN],
            ),
            TongueDetection(
                class_id=10, label="huangtaishe", name=_LBL_HUANGTAI, confidence=0.6311,
                meaning=BilingualText(
                    zh="舌苔偏黄，常作为湿热或里热的观察信号。",
                    en="A yellow coating is often seen as a sign of damp-heat or interior heat.",
                ),
                possible_risks=[_RISK_HEAT],
            ),
            TongueDetection(
                class_id=7, label="liewenshe", name=_LBL_LIEWEN, confidence=0.4452,
                meaning=BilingualText(
                    zh="舌面裂纹明显，常作为津液不足、阴虚或长期消化吸收状态异常的观察信号。",
                    en="A cracked tongue is often seen as a sign of insufficient body fluids, yin deficiency, or abnormal digestive function.",
                ),
                possible_risks=[_RISK_FLUIDS, _RISK_YIN],
            ),
        ],
    ),
    # Variant 3 — Yang-deficiency with damp-phlegm presentation.
    TongueAnalysis(
        detected_labels=[
            TongueDetectedLabel(name=_LBL_PANGDA, count=1),
            TongueDetectedLabel(name=_LBL_BAITAI, count=1),
            TongueDetectedLabel(name=_LBL_CHIHEN, count=2),
        ],
        possible_disease_or_health_risks=[
            TongueHealthRisk(risk=_RISK_PHLEGM,      score=1.310),
            TongueHealthRisk(risk=_RISK_DAMP_SPLEEN, score=1.245),
            TongueHealthRisk(risk=_RISK_COLD_DAMP,   score=0.880),
        ],
        detections=[
            TongueDetection(
                class_id=5, label="pangdashe", name=_LBL_PANGDA, confidence=0.7102,
                meaning=BilingualText(
                    zh="舌体胖大，常作为阳虚、水湿内停或痰湿体质的观察信号。",
                    en="An enlarged tongue is often seen as a sign of yang deficiency, internal water retention, or a phlegm-damp constitution.",
                ),
                possible_risks=[_RISK_PHLEGM, _RISK_DAMP_SPLEEN],
            ),
            TongueDetection(
                class_id=9, label="baitaishe", name=_LBL_BAITAI, confidence=0.6203,
                meaning=BilingualText(
                    zh="舌苔偏白，常作为寒湿、脾胃功能偏弱或早期外感的观察信号。",
                    en="A white coating on the tongue is often seen as a sign of cold-dampness, weak spleen function, or early external contraction.",
                ),
                possible_risks=[_RISK_COLD_DAMP],
            ),
            TongueDetection(
                class_id=8, label="chihenshe", name=_LBL_CHIHEN, confidence=0.3318,
                meaning=BilingualText(
                    zh="舌边齿痕明显，常作为脾虚、湿重或水液代谢偏弱的观察信号。",
                    en="A dentate tongue is often seen as a sign of spleen deficiency, excessive dampness, or weak water metabolism.",
                ),
                possible_risks=[_RISK_DAMP_SPLEEN],
            ),
        ],
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


def mock_diagnosis(
    session_id: str,
    patient: PatientInfo,
    tongue: Optional[TongueAnalysis],
    pulse: Optional[PulseAnalysis],
) -> tuple[BilingualText, BilingualText, DiagnosisAdvice]:
    # Seed off the top detected label's English name when available — that's
    # the strongest single-token summary of the tongue analysis.
    top_label = (
        tongue.detected_labels[0].name.en
        if tongue and tongue.detected_labels
        else None
    )
    seed = (
        f"dx:{session_id}:{patient.age}:{patient.gender}:{top_label}"
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
