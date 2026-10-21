"""Structured telemetry. Logs locally; Haydn sink is a later swap.

Logging vs telemetry:
- Logging (app.core.logging) is for humans debugging a single request.
- Telemetry is a fixed-shape event per request, meant to be shipped to a
  monitoring service (Haydn Observability Cloud) and counted/graphed:
  requests per endpoint, failure rate, latency, and so on.

Week 1 (Task 5): one event per request with request_id, endpoint, and
success/failure. Later: prompt_hash, response_hash, retrieval chunk IDs,
token estimate, safety flags.
"""

from typing import Any

from app.core.logging import get_logger

logger = get_logger("telemetry")


def emit(event: dict[str, Any]) -> None:
    """Write a structured event. Replace the body with Haydn Observability Cloud."""
    # Later: POST or OTel export to HAYDN_ENDPOINT using HAYDN_API_KEY.
    logger.info("telemetry", extra=event)


def emit_request(
    *,
    request_id: str,
    endpoint: str,
    success: bool,
    error_code: str | None = None,
    latency_ms: int | None = None,
) -> None:
    """Task 5: record the outcome of one API request.

    Every request produces exactly one event, whether it succeeded, was
    blocked by the quota, or crashed. Keeping the same keys every time
    makes the events easy to count and chart later.
    """
    emit(
        {
            "event": "request_completed",
            "request_id": request_id,
            "endpoint": endpoint,
            "success": success,
            # NULL on success; e.g. "QUOTA_EXCEEDED" or "INTERNAL_ERROR" on failure.
            "error_code": error_code,
            "latency_ms": latency_ms,
        }
    )
