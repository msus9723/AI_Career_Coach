"""Structured telemetry. Logs locally; Haydn sink is a later swap.

Emit: request_id, prompt_hash, response_hash, retrieval chunk IDs,
latency, token estimate, safety flags, error codes.
"""

from typing import Any

from app.core.logging import get_logger

logger = get_logger("telemetry")


def emit(event: dict[str, Any]) -> None:
    """Write a structured event. Replace the body with Haydn Observability Cloud."""
    # Later: POST or OTel export to HAYDN_ENDPOINT using HAYDN_API_KEY.
    logger.info("telemetry", extra=event)
