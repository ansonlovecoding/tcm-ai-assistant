# TCM Diagnosis API

FastAPI backend for the Qi-Huang AI / 岐黄智诊 web app. All analyses are mocked.

## Run

```bash
# from repo root
./api/run.sh
```

Default URL: <http://localhost:8000>
Interactive docs: <http://localhost:8000/docs>

## Endpoints

| Method | Path                                       | Purpose                                     |
|-------:|--------------------------------------------|---------------------------------------------|
|   GET  | `/api/health`                              | Liveness check                              |
|  POST  | `/api/sessions`                            | Create a session with patient basic info    |
|  POST  | `/api/sessions/{id}/tongue`                | Upload tongue image (multipart) + analysis  |
|  POST  | `/api/sessions/{id}/pulse`                 | Submit pulse capture + analysis             |
|  POST  | `/api/sessions/{id}/diagnose`              | Generate the final pattern report           |
|   GET  | `/api/sessions/{id}`                       | Inspect the full session state              |

All text fields that surface in the UI are returned as `{ "zh": "...", "en": "..." }`
so the frontend can pick the right language on the fly.
