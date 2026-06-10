import json
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

from api.app.models import PatientInfo, TongueAnalysis, PulseAnalysis
from ai_llm import rag

if not os.getenv("DEEPSEEK_API_KEY"):
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    load_dotenv(os.path.join(BASE_DIR, ".env"))

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """你是一位精通传统中医辨证论治的AI助手。请根据患者信息、舌象检测结果、知识库检索依据和脉象分析，综合进行中医辨证，给出专业的证型判断和调理建议。

重要规则：
- 舌象的含义和风险解读必须以【知识库依据】部分的书籍原文内容为准，不得自行编造
- 若知识库中无对应依据，须在 summary 中注明"当前知识库无对应记录"
- 不得将舌象检测结果直接等同于疾病诊断
- 输出结论时应说明依据来源和适用限制

输出规则：
- 必须以合法JSON格式输出，不含任何markdown代码块或多余文字
- 所有用户可见字段必须同时提供zh（中文）和en（英文）两种语言
- 证型（pattern）使用标准中医术语，要精确
- 建议（advice）分生活作息、饮食、代茶饮三类，要实际可行

输出结构：
{
  "pattern":  {"zh": "...", "en": "..."},
  "summary":  {"zh": "...", "en": "..."},
  "advice": {
    "lifestyle":  {"zh": "...", "en": "..."},
    "diet":       {"zh": "...", "en": "..."},
    "herbal_tea": {"zh": "...", "en": "..."}
  },
  "food_recommendations": {
    "zh": ["推荐食物1", "推荐食物2", "推荐食物3", "推荐食物4", "推荐食物5"],
    "en": ["Food 1", "Food 2", "Food 3", "Food 4", "Food 5"]
  },
  "foods_to_avoid": {
    "zh": ["忌食食物1", "忌食食物2", "忌食食物3", "忌食食物4"],
    "en": ["Food 1", "Food 2", "Food 3", "Food 4"]
  },
  "disclaimer": {
    "zh": "本报告由AI生成，仅供学习与参考，不构成医疗诊断。请咨询执业中医师。",
    "en": "AI-generated for reference only. Not a medical diagnosis. Please consult a licensed TCM practitioner."
  }
}

food_recommendations 和 foods_to_avoid 必须是具体食物名称的列表，每项只写食物名，不加说明文字。"""


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_rag_context(evidence: list) -> str:
    if not evidence:
        return ""
    lines = ["\n【知识库依据】（来源：本地中医文献向量检索，请以此解读舌象含义）"]
    for i, item in enumerate(evidence, 1):
        src  = item.get("source", "")
        text = item.get("text", "")
        sim  = item.get("similarity", 0.0)
        lines.append(f"  [{i}] 来源：{src}（相似度 {sim:.2f}）\n      {text}")
    lines.append(
        "\n请依据以上书籍内容解释舌象，不把舌象检测直接等同于疾病诊断，"
        "输出结论时说明依据来源和适用限制。"
    )
    return "\n".join(lines)


def _build_prompt(
    patient: PatientInfo,
    tongue_ml: Optional[TongueAnalysis],
    pulse_analysis: Optional[PulseAnalysis],
    evidence: Optional[list] = None,
) -> str:
    age    = patient.age
    gender = patient.gender
    height = patient.height
    weight = patient.weight
    bmi    = weight / ((height / 100) ** 2) if height else 0

    lines = [f"【患者基本信息】\n年龄：{age}岁 | 性别：{gender} | 身高：{height}cm | 体重：{weight}kg | BMI：{bmi:.1f}"]

    if tongue_ml:
        # Only label / name / count / confidence — meaning and risks come from RAG
        label_summary = "、".join(
            d.name.zh for d in tongue_ml.detected_labels
        ) or "未检测到异常"
        count_lines = "\n".join(
            f"  - {d.name.zh}（{d.name.en}）× {d.count}"
            for d in tongue_ml.detected_labels
        )
        det_lines = "\n".join(
            f"  - {d.label}: {d.name.zh}（置信度 {d.confidence:.0%}）"
            for d in tongue_ml.detections
        )
        lines.append(
            f"\n【舌象检测结果】（来源：机器学习视觉模型，仅提供标签和置信度）\n"
            f"检测到特征：{label_summary}\n"
            f"计数统计：\n{count_lines}\n"
            f"检测详情：\n{det_lines}"
        )
        if evidence:
            lines.append(_build_rag_context(evidence))
    else:
        lines.append("\n【舌象分析】\n暂无舌象数据。")

    if pulse_analysis:
        sbp = pulse_analysis.sbp
        dbp = pulse_analysis.dbp
        if sbp is not None and dbp is not None:
            lines.append(
                f"\n【脉象分析】（来源：血压预测模型）\n"
                f"收缩压（SBP）：{sbp} mmHg | 舒张压（DBP）：{dbp} mmHg"
            )
        else:
            lines.append("\n【脉象分析】\n暂无血压数据。")
    else:
        lines.append("\n【脉象分析】\n暂无脉象数据。")

    lines.append("\n请综合以上信息进行中医辨证，以JSON格式输出。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

async def generate_diagnosis(
    session_id: str,
    patient: PatientInfo,
    tongue_ml: Optional[TongueAnalysis] = None,
    pulse_analysis: Optional[PulseAnalysis] = None,
) -> dict:
    """Call DeepSeek to generate a TCM pattern report with local RAG evidence."""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY 未配置")

    detected_labels = list({d.label for d in tongue_ml.detections if d.label}) if tongue_ml else []
    evidence = rag.retrieve(detected_labels, top_k=5)

    client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
    resp = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_prompt(patient, tongue_ml, pulse_analysis, evidence)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    data = json.loads(resp.choices[0].message.content)
    data["session_id"]           = session_id
    data["generated_at"]         = datetime.now(timezone.utc).isoformat()
    data["pattern"]              = data.get("pattern", {"zh": "", "en": ""})
    data["summary"]              = data.get("summary", {"zh": "", "en": ""})
    data["advice"]               = data.get("advice", {"zh": "", "en": ""})
    data["disclaimer"]           = data.get("disclaimer", {"zh": "", "en": ""})
    data["food_recommendations"] = data.get("food_recommendations", {"zh": [], "en": []})
    data["foods_to_avoid"]       = data.get("foods_to_avoid", {"zh": [], "en": []})
    data["evidence"]             = evidence
    return data

