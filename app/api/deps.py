"""API-key auth and per-user daily quota (in-memory Week 1 stub).

Swap the quota store for Redis when you deploy more than one process.
"""

from collections import defaultdict
from datetime import date, datetime, timezone

from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings

_quota_day: date | None = None
_quota_counts: dict[str, int] = defaultdict(int)


def _reset_quota_if_new_day() -> None:
    global _quota_day, _quota_counts
    today = datetime.now(timezone.utc).date()
    if _quota_day != today:
        _quota_day = today
        _quota_counts = defaultdict(int)


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    if not x_api_key or x_api_key not in settings.api_key_set:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_api_key


def enforce_daily_quota(user_id: str | None, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    _reset_quota_if_new_day()
    key = user_id or "anonymous"
    if _quota_counts[key] >= settings.daily_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily quota exceeded",
        )
    _quota_counts[key] += 1
