<<<<<<< HEAD
# AI_Career_Coach
Build a cloud‑deployable AI Career Coach that compares a user’s resume with a job description, identifies skill gaps, recommends roles, and suggests learning paths. The app must include RAG, agentic workflows, safety checks, and monitoring/telemetry.
=======
# AI Career Coach — Week 1 FastAPI skeleton

Compares a resume with a job description via `POST /compare`. Orchestration, RAG, safety classifiers, and prompt templates are **not** implemented yet (HTTP 501).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Try it

Health (no auth):

```bash
curl -s http://127.0.0.1:8000/health
```

Compare (expect 501 until you implement `app.services.orchestrator.compare`):

```bash
curl -s -X POST http://127.0.0.1:8000/compare \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me" \
  -d '{"resume_text":"...", "job_description_text":"...","user_id":"meera"}'
```

## Docker

```bash
docker build -t ai-career-coach .
docker run --rm -p 8000:8000 --env-file .env ai-career-coach
```

TLS / HTTPS belongs on the reverse proxy or cloud load balancer, not in Uvicorn for this skeleton.

## What you fill in

| Area | Where |
| --- | --- |
| Agent orchestration | `app/services/orchestrator.py` |
| Chunk / embed / retrieve | `app/services/rag.py` |
| Safety checks | `app/services/safety.py` |
| Telemetry design + Haydn sink | `app/services/telemetry.py` |
| Prompt templates | `app/prompts/` |
| Tools | `app/services/tools.py` |
| Real PII redaction | `app/core/security.py` |

## Security hooks already wired

- API key: `X-API-Key` vs `API_KEYS` in env
- Per-user daily quota (in-memory)
- `slowapi` rate limit on `/compare`
- PII redaction called before orchestration (identity function today)
- Secrets via environment variables

## Refactor later

- Point `DATABASE_URL` at Postgres when you leave SQLite; add Alembic once the schema settles
- Move daily quota to Redis so multiple workers share a counter
- Split `tools.py` when skill extractor / comparator / search have real implementations
- Export telemetry with OpenTelemetry to Haydn Observability Cloud instead of stdout JSON
- Add a small monitoring dashboard once events are in Haydn or Postgres
>>>>>>> ee3f60c (add FastAPI project skeleton and stubs)
