FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libs required by the sibling packages we import:
#   libgl1 / libglib2.0-0 — OpenCV (ultralytics dep, used by tongue's YOLO subprocess)
#   libgomp1              — torch (pulse predictor) + numpy thread pools
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install all Python deps for the api itself **and** every sibling package
# main.py imports: ai_agent (openai, python-dotenv), pulse (torch, numpy,
# matplotlib) and tongue (ultralytics, opencv, Pillow, PyYAML).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code is bind-mounted by docker-compose at runtime so hot-reload
# works without rebuilding. The expected layout inside the container is:
#
#   /app/
#   ├── api/app/...    (mounted from ./api/app)
#   ├── ai_agent/...   (mounted from ./ai_agent)
#   ├── pulse/...      (mounted from ./pulse)
#   └── tongue/...     (mounted from ./tongue)
#
# To build a fully self-contained image (no compose / no bind mounts), set
# the build context to the repo root in compose:
#
#   build:
#     context: .
#     dockerfile: api/Dockerfile
#
# and add these COPY lines back above the EXPOSE line:
#
COPY api/app   ./api/app
COPY ai_agent  ./ai_agent
COPY pulse     ./pulse
COPY tongue    ./tongue

EXPOSE 8000

# Run via `python -m uvicorn` so the CWD (/app) is on sys.path — that's what
# lets `import api.app.main`, `import ai_agent.agent`, `import pulse.predict`,
# `import tongue.predict_result_from_bytes` all resolve from the same root.
CMD ["python", "-m", "uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
