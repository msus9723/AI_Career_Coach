# AI Career Coach

Build a cloud‑deployable AI Career Coach that compares a user’s resume with a job description, identifies skill gaps, recommends roles, and suggests learning paths. The app must include RAG, agentic workflows, safety checks, and monitoring/telemetry.

## Current state (Week 1)

`POST /gap-analysis` runs the full request pipeline, but the analysis itself is a placeholder:

1. PII redaction (emails, phone numbers)
2. Per-user daily quota, counted in SQLite
3. Placeholder response
4. Interaction saved to SQLite (`interactions` table)
5. Structured JSON log line + telemetry event, all sharing one `request_id`

A Streamlit UI (`ui/`) lets you paste a resume and job description and see the result.

## Project layout

| Part | Where |
| --- | --- |
| HTTP routes | `app/api/routes/` |
| Orchestrator (pipeline + future agent logic) | `app/services/orchestrator.py` |
| Daily quota | `app/services/quota.py` |
| PII redaction, rate limiter | `app/core/security.py` |
| Telemetry | `app/services/telemetry.py` |
| DB models | `app/db/models.py` |
| Streamlit UI | `ui/app.py` |
| RAG, tools, safety (stubs) | `app/services/rag.py`, `tools.py`, `safety.py` |

## Run locally (no Docker)

The API and the UI use **separate** virtual environments: Streamlit needs a newer `starlette` than FastAPI 0.115 allows.

API (terminal 1):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --reload-dir app
```

`--reload-dir app` restarts the server only when code in `app/` changes, not when packages inside `.venv-ui/` change.

UI (terminal 2):

```bash
python3 -m venv .venv-ui
source .venv-ui/bin/activate
pip install -r ui/requirements.txt
streamlit run ui/app.py
```

Run it from the project root: the path is `ui/app.py` (a slash, not `ui.app.py`), and `.streamlit/config.toml` is only picked up from there. Streamlit won't open a browser tab by itself.

Open http://localhost:8501 for the UI, or http://localhost:8000/docs for the API's interactive docs.

## Run with Docker

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
docker compose up --build
```

- UI: http://localhost:8501
- API: http://localhost:8000 (docs at `/docs`)

The SQLite database lives in the `coach-data` Docker volume, so it survives restarts. `docker compose down -v` deletes it.

Settings (`API_KEYS`, `DAILY_QUOTA`, `RATE_LIMIT`, ...) are read from `.env` if present; see `.env.example`.

TLS / HTTPS belongs on the reverse proxy or cloud load balancer, not in Uvicorn.

## Try the API directly

```bash
curl -s -X POST http://127.0.0.1:8000/gap-analysis \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d '{"resume_text":"...", "job_description_text":"...", "user_id":"meera"}'
```

Status codes: `200` placeholder result, `401` bad API key, `422` invalid input, `429` daily quota or rate limit exceeded.

## Resetting the database

The schema has no migrations yet. After changing `app/db/models.py`, stop the server and delete `data/coach.db` (or `docker compose down -v`); tables are recreated on startup.

## Next

- RAG with LlamaIndex in `app/services/rag.py`, called from the orchestrator
- LLM-generated gap analysis, tools, and safety checks
- Remove the legacy `/compare` route

## Refactor later

- Point `DATABASE_URL` at Postgres when you leave SQLite; add Alembic once the schema settles
- Export telemetry with OpenTelemetry to Haydn Observability Cloud instead of stdout JSON
- Add a small monitoring dashboard once events are in Haydn or Postgres
