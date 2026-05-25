# TCM AI Agent 使用说明

底层 LLM 使用 **DeepSeek V3**（`deepseek-chat`），通过 OpenAI 兼容接口调用。

## 安装依赖

```bash
pip install -r aiagent/requirements.txt
```

## 配置 API Key

在 `aiagent/` 目录下创建 `.env` 文件，填入 DeepSeek API Key：

```
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

API Key 可在 [platform.deepseek.com](https://platform.deepseek.com) 获取。

## 调用方式

```python
from aiagent.agent import generate_diagnosis

result = await generate_diagnosis(
    session_id="abc123",
    patient={
        "age": 32,
        "gender": "female",
        "height": 165,
        "weight": 54
    },
    tongue_ml={...},        # 舌象 ML 模型输出的 JSON，可不传
    pulse_analysis={...},   # 脉象分析数据（含 sbp/dbp），可不传
)
```

> `generate_diagnosis` 是异步函数，需要 `await` 调用。

## 返回格式

```json
{
  "session_id": "abc123",
  "pattern": { "zh": "湿热内蕴证", "en": "Damp-Heat Accumulation Pattern" },
  "summary": { "zh": "...", "en": "..." },
  "advice": {
    "lifestyle":  { "zh": "...", "en": "..." },
    "diet":       { "zh": "...", "en": "..." },
    "herbal_tea": { "zh": "...", "en": "..." }
  },
  "food_recommendations": {
    "zh": ["冬瓜", "绿豆", "苦瓜", "莲藕", "茯苓"],
    "en": ["Winter melon", "Mung beans", "Bitter melon", "Lotus root", "Poria"]
  },
  "foods_to_avoid": {
    "zh": ["辣椒", "油炸食品", "烧烤", "酒精"],
    "en": ["Chili peppers", "Fried foods", "Barbecue", "Alcohol"]
  },
  "disclaimer": { "zh": "...", "en": "..." },
  "generated_at": "2026-05-25T08:00:00+00:00"
}
```

返回结果可直接用于：

```python
return DiagnosisResult(**result)
```

## pulse_analysis 格式

脉搏模型目前输出血压预测结果，传入以下格式即可：

```json
{
  "sbp": 128,
  "dbp": 82
}
```

| 字段  | 含义                        | 单位  |
|-------|-----------------------------|-------|
| `sbp` | 收缩压（Systolic BP，高压） | mmHg  |
| `dbp` | 舒张压（Diastolic BP，低压）| mmHg  |

agent 会在 prompt 中以如下形式传给 DeepSeek，让模型结合血压进行辨证：

```
【脉象分析】（来源：血压预测模型）
收缩压（SBP）：128 mmHg | 舒张压（DBP）：82 mmHg
```

## tongue_ml 格式

即 ML 模型输出的 `predict_result.json` 内容，直接传入即可：

```json
{
  "risk_level": "mild_attention",
  "summary": "检测到舌象异常信号，优先关注：湿热风险、胃肠积热风险",
  "detected_labels": { "黄苔舌": 1 },
  "possible_disease_or_health_risks": [
    { "risk": "湿热风险", "score": 2.572 }
  ],
  "detections": [
    {
      "name": "黄苔舌",
      "confidence": 0.8575,
      "meaning": "舌苔偏黄，常作为湿热、胃肠积热或炎症状态的观察信号。",
      "possible_risks": ["湿热风险", "胃肠积热风险"]
    }
  ]
}
```
