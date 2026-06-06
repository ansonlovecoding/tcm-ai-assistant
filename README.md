# TCM AI LLM 使用说明

底层 LLM 使用 **DeepSeek V3**（`deepseek-chat`），通过 OpenAI 兼容接口调用。
本模块在 LLM 层加入了本地向量 RAG（检索增强生成），知识库来源为 `kb/tongue_profiles.json`。

## 模块结构

```
ai_llm/
├── agent.py              # 主入口，调用 RAG + DeepSeek 生成报告
├── rag.py                # 本地 TF-IDF 向量检索模块
└── kb/
    └── tongue_profiles.json  # 20 类舌象知识库
```

## 安装依赖

```bash
pip install -r api/requirements.txt
```

## 配置 API Key

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

## 调用方式

```python
from ai_llm.agent import generate_diagnosis

result = await generate_diagnosis(
    session_id="abc123",
    patient=PatientInfo(age=32, gender="female", height=165, weight=54),
    tongue_ml=tongue_analysis,   # TongueAnalysis 对象，可不传
    pulse_analysis=pulse_analysis,  # PulseAnalysis 对象，可不传
)
```

## RAG 工作流程

1. 从 `tongue_ml.detections` 提取 `label` 和 `confidence`（不使用模型自带的 meaning/risks）
2. `rag.retrieve()` 对每个 label 做精确匹配，未命中则用 TF-IDF cosine 相似度检索
3. 检索到的知识库文档作为 RAG Context 注入 LLM prompt
4. LLM 依据 RAG 内容生成报告，检索依据原样写入 `evidence` 字段

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
  "food_recommendations": { "zh": ["冬瓜", "..."], "en": ["Winter melon", "..."] },
  "foods_to_avoid":       { "zh": ["辣椒", "..."], "en": ["Chili peppers", "..."] },
  "disclaimer": { "zh": "...", "en": "..." },
  "generated_at": "2026-06-05T08:00:00+00:00",
  "evidence": [
    {
      "label": "chihenshe",
      "name": { "zh": "齿痕舌", "en": "Dentate tongue" },
      "meaning": { "zh": "舌边齿痕明显…", "en": "A dentate tongue…" },
      "risks": [
        { "zh": "脾虚湿重风险", "en": "Risk of Spleen Deficiency and Excessive Dampness" }
      ],
      "confidence": 0.86,
      "similarity": 1.0,
      "source": "local_vector_kb:tongue_profiles"
    }
  ]
}
```

`similarity = 1.0` 表示精确匹配；`< 1.0` 表示 TF-IDF 相似度回退。
