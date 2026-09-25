import hashlib
import json
import time
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import enforce_daily_quota, require_api_key
from app.core.security import limiter, redact_pii
from app.core.config import get_settings
from app.db.models import Interaction, Metric, SafetyFlag
from app.db.session import get_db
from app.schemas.compare import CompareRequest, CompareResponse, TelemetryMetadata
from app.services import orchestrator, telemetry

router = APIRouter(tags=["compare"])


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@router.post("/compare", response_model=CompareResponse)
@limiter.limit(get_settings().rate_limit)
def compare(
    request: Request,
    payload: CompareRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[str, Depends(require_api_key)],
) -> CompareResponse:
    request_id = str(uuid.uuid4())
    started = time.perf_counter()

    resume = redact_pii(payload.resume_text)
    job_description = redact_pii(payload.job_description_text)
    redacted = payload.model_copy(
        update={"resume_text": resume, "job_description_text": job_description}
    )
    enforce_daily_quota(redacted.user_id)

    error_code: str | None = None
    result: CompareResponse | None = None
    try:
        result = orchestrator.compare(redacted, request_id)
    except NotImplementedError:
        error_code = "NOT_IMPLEMENTED"
        latency_ms = int((time.perf_counter() - started) * 1000)
        result = CompareResponse(
            telemetry=TelemetryMetadata(
                request_id=request_id,
                prompt_hash=_hash_text(resume + job_description),
                latency_ms=latency_ms,
                error_code=error_code,
            )
        )

    latency_ms = result.telemetry.latency_ms or int(
        (time.perf_counter() - started) * 1000
    )
    interaction = Interaction(
        user_id=redacted.user_id,
        resume_hash=_hash_text(resume),
        jd_hash=_hash_text(job_description),
        prompt_hash=result.telemetry.prompt_hash,
        response_hash=result.telemetry.response_hash,
        redacted_resume_snippet=resume[:500] or None,
        redacted_jd_snippet=job_description[:500] or None,
        response_json=result.model_dump_json() if error_code is None else None,
        error_code=result.telemetry.error_code or error_code,
    )
    db.add(interaction)
    db.flush()

    for flag in result.safety_flags:
        db.add(
            SafetyFlag(
                interaction_id=interaction.id,
                flag_type=flag.flag_type,
                score=flag.score,
                metadata_json=json.dumps(flag.metadata) if flag.metadata else None,
            )
        )
    db.add(
        Metric(
            interaction_id=interaction.id,
            latency_ms=latency_ms,
            token_estimate=result.telemetry.token_estimate,
            chunk_ids_json=json.dumps(result.telemetry.chunk_ids)
            if result.telemetry.chunk_ids
            else None,
        )
    )
    db.commit()

    telemetry.emit(
        {
            "request_id": request_id,
            "prompt_hash": result.telemetry.prompt_hash,
            "response_hash": result.telemetry.response_hash,
            "chunk_ids": result.telemetry.chunk_ids,
            "latency_ms": latency_ms,
            "token_estimate": result.telemetry.token_estimate,
            "safety_flags": [f.flag_type for f in result.safety_flags],
            "error_code": result.telemetry.error_code or error_code,
        }
    )

    if error_code == "NOT_IMPLEMENTED":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": "Coach orchestration is not implemented yet",
                "telemetry": result.telemetry.model_dump(),
            },
        )
    return result
