import json
import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """你是一位精通传统中医辨证论治的AI助手。请根据患者信息、舌象检测结果和脉象分析，综合进行中医辨证，给出专业的证型判断和调理建议。

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

def _build_prompt(patient: dict, tongue_ml: Optional[dict], pulse_analysis: Optional[dict]) -> str:
    age    = patient.get("age", "未知")
    gender = patient.get("gender", "未知")
    height = patient.get("height", 0)
    weight = patient.get("weight", 0)
    bmi    = weight / ((height / 100) ** 2) if height else 0

    lines = [f"【患者基本信息】\n年龄：{age}岁 | 性别：{gender} | 身高：{height}cm | 体重：{weight}kg | BMI：{bmi:.1f}"]

    if tongue_ml:
        labels  = "、".join(tongue_ml.get("detected_labels", {}).keys()) or "未检测到异常"
        risks   = "、".join(d.get("risk", "") for d in tongue_ml.get("possible_disease_or_health_risks", []))
        details = "\n".join(
            f"  - {d.get('name')}（置信度 {d.get('confidence', 0):.0%}）：{d.get('meaning', '')}"
            for d in tongue_ml.get("detections", [])
        )
        lines.append(
            f"\n【舌象分析】（来源：机器学习视觉检测模型）\n"
            f"风险等级：{tongue_ml.get('risk_level', '')}\n"
            f"检测摘要：{tongue_ml.get('summary', '')}\n"
            f"检测到特征：{labels}\n"
            f"健康风险提示：{risks}\n"
            f"详细检测：\n{details}"
        )
    else:
        lines.append("\n【舌象分析】\n暂无舌象数据。")

    if pulse_analysis:
        pt = pulse_analysis.get("pulse_type", {})
        lines.append(
            f"\n【脉象分析】\n"
            f"脉型：{pt.get('zh', '')} | 心率：{pulse_analysis.get('rate_bpm', '')}次/分\n"
            f"节律：{pulse_analysis.get('rhythm', {}).get('zh', '')} | "
            f"力度：{pulse_analysis.get('strength', {}).get('zh', '')}\n"
            f"备注：{pulse_analysis.get('notes', {}).get('zh', '')}"
        )
    else:
        lines.append("\n【脉象分析】\n暂无脉象数据。")

    lines.append("\n请综合以上信息进行中医辨证，以JSON格式输出。")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main function — import 后直接调用这个
# ---------------------------------------------------------------------------

async def generate_diagnosis(
    session_id: str,
    patient: dict,
    tongue_ml: Optional[dict] = None,
    pulse_analysis: Optional[dict] = None,
) -> dict:
    """
    调用 OpenAI 生成中医辨证报告。

    参数：
        session_id     - 会话 ID（原样带回响应）
        patient        - 患者信息 {"age": 32, "gender": "female", "height": 165, "weight": 54}
        tongue_ml      - ML 模型输出的舌象 JSON（predict_result.json 的内容），可选
        pulse_analysis - 脉象分析对象（现有 API Step 3 返回的 analysis 字段），可选

    返回：
        与现有 DiagnosisResult 格式一致的 dict，可直接传给 DiagnosisResult(**result)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 未配置")

    client = AsyncOpenAI(api_key=api_key)

    resp = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_prompt(patient, tongue_ml, pulse_analysis)},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    data = json.loads(resp.choices[0].message.content)
    data["session_id"]           = session_id
    data["generated_at"]         = datetime.now(timezone.utc).isoformat()
    data["food_recommendations"] = data.get("food_recommendations", {"zh": [], "en": []})
    data["foods_to_avoid"]       = data.get("foods_to_avoid", {"zh": [], "en": []})
    return data
