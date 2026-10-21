"""POST /gap-analysis: the HTTP layer only.

This route handles the "web" concerns: checking the API key, rate limiting,
validating the JSON body, and turning errors into HTTP status codes. All of
the actual work (redaction, quota, saving, logging) happens in
app.services.orchestrator.run_gap_analysis (Task 6).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_api_key
from app.core.config import get_settings
from app.core.security import limiter
from app.db.session import get_db
from app.schemas.gap_analysis import GapAnalysisRequest, GapAnalysisResponse
from app.services import orchestrator
from app.services.quota import QuotaExceededError

router = APIRouter(tags=["gap-analysis"])


@router.post("/gap-analysis", response_model=GapAnalysisResponse)
# Per-IP rate limit from RATE_LIMIT in .env (e.g. "10/minute").
@limiter.limit(get_settings().rate_limit)
def gap_analysis(
    # slowapi needs the raw Request object to work out the caller's IP,
    # so keep this parameter even though the function body doesn't use it.
    request: Request,
    payload: GapAnalysisRequest,
    # A SQLite session, opened per request and closed afterwards.
    # Passed to the orchestrator for the quota check and the interaction save.
    db: Annotated[Session, Depends(get_db)],
    # Rejects the call with 401 unless the X-API-Key header is valid.
    _: Annotated[str, Depends(require_api_key)],
) -> GapAnalysisResponse:
    # Created here so the same id appears in the response, logs, and DB.
    request_id = str(uuid.uuid4())

    try:
        return orchestrator.run_gap_analysis(payload, db, request_id)
    except QuotaExceededError as exc:
        # The orchestrator raises a plain Python error; choosing the HTTP
        # status code (429) is the route's job.
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Daily quota exceeded",
                "used": exc.used,
                "limit": exc.limit,
                "request_id": request_id,
            },
        ) from exc
