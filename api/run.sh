#!/usr/bin/env bash
# Start the FastAPI dev server.
# Run from the repo root or this directory; uses ../.venv if it exists.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif [[ -x "$ROOT/venv/bin/python" ]]; then
  PY="$ROOT/venv/bin/python"
else
  PY="$(command -v python3.10 || command -v python3)"
fi

cd "$HERE"
exec "$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
