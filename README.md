# TCM AI Assistant · 岐黄智诊

> Traditional Chinese Medicine diagnosis assistant — 中医智能辨证助手
> _Combining tongue observation, pulse analysis and AI-assisted pattern differentiation._

**Languages:** [English](#english) · [中文](#中文)

---

## English

### Project structure

```
code/
├── web/              React + Vite single-page app (Chinese / English bilingual UI)
├── api/              FastAPI service exposing the endpoints consumed by the web app
├── ai-agent/         AI agent that synthesises patient info, tongue and pulse results
│                     into a TCM pattern differentiation
├── tongue-analysis/  Model training & inference for tongue images
├── pulse-analysis/   Model training & inference for pulse waveforms
├── docker-compose.yml
├── .venv/            Local Python 3.10 virtualenv (created by the developer)
└── README.md
```

Module responsibilities:

| Module            | Role                                                                                  |
|-------------------|---------------------------------------------------------------------------------------|
| `web`             | Four-step UI: patient info → tongue photo → pulse capture → AI diagnosis. Traditional Chinese styling, Chinese & English. |
| `api`             | FastAPI HTTP layer. Validates input, stores sessions, returns bilingual analyses.     |
| `ai-agent`        | Orchestrates LLM + retrieval to produce the final pattern report (planned).           |
| `tongue-analysis` | Vision model for tongue body / coating / shape (planned).                             |
| `pulse-analysis`  | Signal-processing & classification of the 28 classical pulse types (planned).         |

### Quick start — Docker

Requires Docker Desktop (or any recent `docker` + `docker compose`).

```bash
docker compose up --build   # first time, or after dep changes
docker compose up           # subsequent runs
docker compose down         # stop and remove containers
```

Once both containers report ready:

- Web UI — <http://localhost:5173>
- API root — <http://localhost:8000>
- Swagger UI — <http://localhost:8000/docs> (see [Interactive API documentation](#interactive-api-documentation-swagger--openapi))

The web service proxies `/api/*` to the api service over the internal compose network, so you only need to open the web URL. Source code is bind-mounted, so editing files on the host triggers live reload in both containers.

### Manual setup (without Docker)

Requires **Python 3.10**, **Node.js 18+** and **npm**.

**1. Create the Python virtual environment** (one-time):

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
```

**2. Start the API** (terminal 1):

```bash
./api/run.sh
# or:
.venv/bin/python -m uvicorn app.main:app --reload --app-dir api --host 0.0.0.0 --port 8000
```

**3. Start the web app** (terminal 2):

```bash
cd web
npm install        # first time
npm run dev
```

Open <http://localhost:5173>. Vite's dev server proxies `/api/*` to the FastAPI server on port 8000.

### API endpoints (summary)

| Method | Path                                  | Purpose                                       |
|--------|---------------------------------------|-----------------------------------------------|
| GET    | `/api/health`                         | Liveness check                                |
| POST   | `/api/sessions`                       | Create a diagnosis session with patient info  |
| POST   | `/api/sessions/{id}/tongue`           | Upload tongue image, returns mock analysis    |
| POST   | `/api/sessions/{id}/pulse`            | Submit pulse capture, returns mock analysis   |
| POST   | `/api/sessions/{id}/diagnose`         | Generate the final pattern report             |
| GET    | `/api/sessions/{id}`                  | Inspect the full session state                |

All user-facing strings are returned as `{ "zh": "...", "en": "..." }`. The web app picks the field for the active locale via `pickLang`.

### Interactive API documentation (Swagger / OpenAPI)

The API is fully described as an OpenAPI 3.1 spec, with tagged endpoints, request/response examples and inline schema descriptions.

| Path             | Tool        | What it is                                                                 |
|------------------|-------------|----------------------------------------------------------------------------|
| `/`              | redirect    | Bounces straight to Swagger UI.                                            |
| `/docs`          | Swagger UI  | Browse endpoints and use **Try it out** to call them straight from the browser. |
| `/redoc`         | ReDoc       | Reference-style three-column layout, good for reading.                     |
| `/openapi.json`  | spec        | Raw OpenAPI document — feed it to Postman, code generators, etc.           |

Once the API is running:

```bash
open http://localhost:8000/docs    # macOS — or just visit it in the browser
```

Endpoints are grouped by tag (`Health` · `Sessions` · `Tongue` · `Pulse` · `Diagnose`) and every request and response model carries a worked example, so **Try it out** pre-fills sensible values for clicking through the whole four-step flow.

### Disclaimer

This project is for **research and educational purposes only**. The AI output does **not** constitute a medical diagnosis. Always consult a licensed TCM practitioner.

---

## 中文

### 项目结构

```
code/
├── web/              React + Vite 单页面应用（中英双语界面）
├── api/              FastAPI 服务，向 web 端提供所需接口
├── ai-agent/         智能体：根据基本信息、舌象与脉象生成中医辨证报告
├── tongue-analysis/  舌象图像模型的训练与推理
├── pulse-analysis/   脉象信号的训练与推理
├── docker-compose.yml
├── .venv/            本地 Python 3.10 虚拟环境（开发者自行创建）
└── README.md
```

模块职责：

| 模块               | 说明                                                                         |
|--------------------|------------------------------------------------------------------------------|
| `web`              | 四步式问诊界面：基本信息 → 舌象采集 → 脉象采集 → 智能辨证。古典中医风格，中英双语。 |
| `api`              | FastAPI 接口层，校验请求、维护会话、返回中英双语的辨证数据。                  |
| `ai-agent`         | 调度 LLM 与知识检索，输出综合辨证报告（规划中）。                            |
| `tongue-analysis`  | 舌质、舌苔、舌形的视觉模型（规划中）。                                       |
| `pulse-analysis`   | 二十八脉的信号处理与分类（规划中）。                                         |

### 快速启动 — Docker

需要安装 Docker Desktop（或较新版本的 `docker` 与 `docker compose`）。

```bash
docker compose up --build   # 首次构建，或依赖变更后
docker compose up           # 之后可直接启动
docker compose down         # 关闭并移除容器
```

待两个容器就绪后：

- 网页 — <http://localhost:5173>
- API 根路径 — <http://localhost:8000>
- Swagger UI — <http://localhost:8000/docs>（详见[交互式 API 文档](#交互式-api-文档swagger--openapi)）

web 容器通过内部网络将 `/api/*` 转发至 api 容器，所以只需访问网页地址即可。源码以 bind-mount 方式挂载，宿主机上编辑文件即可在两个容器中触发热更新。

### 手动启动（不使用 Docker）

需要 **Python 3.10**、**Node.js 18+** 与 **npm**。

**1. 创建 Python 虚拟环境**（仅首次）：

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r api/requirements.txt
```

**2. 启动 API**（终端 1）：

```bash
./api/run.sh
# 或：
.venv/bin/python -m uvicorn app.main:app --reload --app-dir api --host 0.0.0.0 --port 8000
```

**3. 启动 Web 应用**（终端 2）：

```bash
cd web
npm install        # 仅首次
npm run dev
```

浏览器访问 <http://localhost:5173>。Vite 开发服务器会将 `/api/*` 转发到 8000 端口的 FastAPI 服务。

### API 接口一览

| 方法   | 路径                                  | 用途                                           |
|--------|---------------------------------------|------------------------------------------------|
| GET    | `/api/health`                         | 健康检查                                       |
| POST   | `/api/sessions`                       | 创建辨证会话（包含基本信息）                   |
| POST   | `/api/sessions/{id}/tongue`           | 上传舌象图片，返回模拟的舌象分析               |
| POST   | `/api/sessions/{id}/pulse`            | 提交脉象采集结果，返回模拟的脉象分析           |
| POST   | `/api/sessions/{id}/diagnose`         | 生成最终辨证报告                               |
| GET    | `/api/sessions/{id}`                  | 查看完整会话信息                               |

所有界面文案以 `{ "zh": "...", "en": "..." }` 的双语形式返回，前端通过 `pickLang` 自动选用当前语言。

### 交互式 API 文档（Swagger / OpenAPI）

API 已完整描述为 OpenAPI 3.1 规范，包含分组标签、示例请求与响应、以及行内字段说明。

| 路径             | 工具         | 说明                                                                       |
|------------------|--------------|----------------------------------------------------------------------------|
| `/`              | 重定向       | 自动跳转到 Swagger UI。                                                    |
| `/docs`          | Swagger UI   | 浏览全部接口，并通过 **Try it out** 在浏览器中直接发起调用。               |
| `/redoc`         | ReDoc        | 三栏式参考文档，更适合阅读。                                              |
| `/openapi.json`  | 原始规范     | OpenAPI 文档原文，可直接导入 Postman、代码生成器等工具。                  |

API 启动后：

```bash
open http://localhost:8000/docs    # macOS — 或直接在浏览器打开
```

接口按标签分组（`Health` · `Sessions` · `Tongue` · `Pulse` · `Diagnose`），每个请求与响应模型都附带示例值，**Try it out** 会自动填入合理参数，可一路点击体验完整的四步流程。

### 免责声明

本项目仅供**学习与研究**使用，AI 输出**不构成**任何形式的医学诊断。如有健康问题，请咨询执业中医师或正规医疗机构。
