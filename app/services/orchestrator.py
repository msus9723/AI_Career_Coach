"""Orchestrator: the "brain" that runs one coaching request end to end.

The route (app/api/routes/gap_analysis.py) only deals with HTTP: auth, rate
limits, parsing JSON, and turning errors into status codes. Everything that
decides *what happens* to a request lives here.

Week 1 flow for run_gap_analysis (Task 6):
    1. redact PII            (app.core.security.redact_pii)
    2. check daily quota     (app.services.quota.check_daily_quota)
    3. build the response    (placeholder for now)
    4. save the interaction  (SQLite `interactions` table, Task 7)
    5. report the outcome    (structured log line, Task 4, + telemetry event, Task 5)

Every request, whether it succeeds, is blocked by the quota, or crashes,
ends with exactly one saved row (best effort), one log line, and one
telemetry event, all sharing the same request_id.

Later weeks slot in between steps 2 and 3: RAG retrieval (services.rag),
tools (services.tools), the LLM call, and safety checks (services.safety).
That's where the actual "agent" logic goes.
"""

import hashlib
import time

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import redact_pii
from app.db.models import Interaction
from app.schemas.compare import CompareRequest, CompareResponse, TelemetryMetadata
from app.schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse
from app.services import telemetry
from app.services.quota import QuotaExceededError, check_daily_quota

logger = get_logger("orchestrator")

ENDPOINT = "/gap-analysis"

# How much redacted text to keep in the DB for debugging. Full text is never
# stored, only a SHA-256 hash, so the table stays small and low-risk.
SNIPPET_CHARS = 500


def _hash_text(value: str) -> str:
    """SHA-256 fingerprint: lets us spot repeated inputs without storing them."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _elapsed_ms(started: float) -> int:
    """Milliseconds since `started` (a time.perf_counter() value)."""
    return int((time.perf_counter() - started) * 1000)


def _save_interaction(
    db: Session,
    *,
    request_id: str,
    user_id: str | None,
    resume: str,
    job_description: str,
    response: GapAnalysisResponse | None,
    error_code: str | None,
    latency_ms: int,
) -> None:
    """Write one row to `interactions`, for successes and failures alike.

    `resume` and `job_description` must already be redacted.
    """
    response_json = response.model_dump_json() if response is not None else None
    db.add(
        Interaction(
            # Task 7: these three columns link the row to logs and telemetry.
            request_id=request_id,
            endpoint=ENDPOINT,
            latency_ms=latency_ms,
            user_id=user_id,
            resume_hash=_hash_text(resume),
            jd_hash=_hash_text(job_description),
            # No LLM prompt exists yet, so there is nothing to hash.
            prompt_hash=None,
            response_hash=_hash_text(response_json) if response_json else None,
            redacted_resume_snippet=resume[:SNIPPET_CHARS] or None,
            redacted_jd_snippet=job_description[:SNIPPET_CHARS] or None,
            response_json=response_json,
            # NULL means success. The quota check only counts NULL rows.
            error_code=error_code,
        )
    )
    db.commit()


def _report_outcome(
    *,
    request_id: str,
    user_id: str | None,
    latency_ms: int,
    error_code: str | None = None,
) -> None:
    """Write the log line (Task 4) and the telemetry event (Task 5) for one request.

    Both happen in this one function, so every exit path of
    run_gap_analysis reports the same way. error_code=None means success.
    """
    success = error_code is None
    logger.info(
        "gap_analysis_request",
        extra={
            "request_id": request_id,
            "user_id": user_id,
            "endpoint": ENDPOINT,
            "outcome": "success" if success else "failure",
            "error_code": error_code,
            "latency_ms": latency_ms,
            # Placeholder: there are no LLM calls yet, so no tokens to count.
            "token_estimate": None,
        },
    )
    telemetry.emit_request(
        request_id=request_id,
        endpoint=ENDPOINT,
        success=success,
        error_code=error_code,
        latency_ms=latency_ms,
    )


def run_gap_analysis(
    payload: GapAnalysisRequest, db: Session, request_id: str
) -> GapAnalysisResponse:
    """Run the Week 1 gap-analysis pipeline and return a placeholder result.

    Raises QuotaExceededError when the user is over today's limit. The
    route turns that into HTTP 429.
    """
    started = time.perf_counter()
    user_id = payload.user_id

    # Step 1: redact first, so nothing below (DB, logs, later the LLM)
    # ever sees raw emails or phone numbers.
    resume = redact_pii(payload.resume_text)
    job_description = redact_pii(payload.job_description_text)

    # Step 2: quota. Blocked requests are still saved (with an error_code)
    # and reported, so there's a record of them. They don't count toward the quota.
    try:
        check_daily_quota(db, user_id)
    except QuotaExceededError:
        latency_ms = _elapsed_ms(started)
        # Saving the "blocked" record is best effort. If the DB write fails,
        # the user must still get the 429 (not a 500), so we log the problem
        # and carry on instead of letting the DB error escape.
        try:
            _save_interaction(
                db,
                request_id=request_id,
                user_id=user_id,
                resume=resume,
                job_description=job_description,
                response=None,
                error_code="QUOTA_EXCEEDED",
                latency_ms=latency_ms,
            )
        except Exception:
            db.rollback()
            logger.warning(
                "failed_to_save_blocked_interaction",
                extra={"request_id": request_id, "user_id": user_id},
                exc_info=True,
            )
        _report_outcome(
            request_id=request_id,
            user_id=user_id,
            latency_ms=latency_ms,
            error_code="QUOTA_EXCEEDED",
        )
        raise

    try:
        # --- Future agent logic goes here (Week 2+) ---
        # chunks = rag.search(...); skills = tools.skill_extractor(...);
        # llm output = ...; flags = safety.evaluate(...)

        # Step 3: placeholder response (Task 8).
        response = GapAnalysisResponse(
            request_id=request_id,
            gap_analysis="Placeholder: gap analysis is not implemented yet.",
            missing_skills=[],
            recommendations=[],
        )

        # Step 4: persist the interaction (Task 7).
        _save_interaction(
            db,
            request_id=request_id,
            user_id=user_id,
            resume=resume,
            job_description=job_description,
            response=response,
            error_code=None,
            latency_ms=_elapsed_ms(started),
        )
    except Exception:
        # Something unexpected broke (e.g. the DB write). Undo the half-done
        # transaction, report the failure, and let the route return a 500.
        db.rollback()
        _report_outcome(
            request_id=request_id,
            user_id=user_id,
            latency_ms=_elapsed_ms(started),
            error_code="INTERNAL_ERROR",
        )
        raise

    # Step 5: report the successful request (log line + telemetry event).
    _report_outcome(request_id=request_id, user_id=user_id, latency_ms=_elapsed_ms(started))
    return response


def compare(payload: CompareRequest, request_id: str) -> CompareResponse:
    """Legacy /compare stub. Still called by app/api/routes/compare.py."""
    _ = (payload, request_id, CompareResponse, TelemetryMetadata)
    raise NotImplementedError(
        "Wire RAG, LLM compare, tools, and safety in app.services.orchestrator.compare"
    )
