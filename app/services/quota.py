"""Per-user daily quota backed by SQLite (Week 1, Task 3).

Instead of keeping counts in memory (lost on restart, not shared between
worker processes), we count how many successful requests the user already
made today by looking at the `interactions` table.

This module deliberately knows nothing about HTTP: it raises
QuotaExceededError. The orchestrator calls it, and the route turns that
error into a 429 response.
"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Interaction


class QuotaExceededError(Exception):
    """Raised when a user has used up today's allowance."""

    def __init__(self, user_id: str | None, used: int, limit: int) -> None:
        self.user_id = user_id
        self.used = used
        self.limit = limit
        super().__init__(f"Daily quota exceeded: {used}/{limit} for user {user_id!r}")


def _start_of_today_utc() -> datetime:
    """Midnight UTC today, as a naive datetime.

    SQLite stores created_at as UTC text without a timezone, so the value we
    compare against must be naive UTC too.
    """
    now = datetime.now(timezone.utc)
    return now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)


def count_requests_today(db: Session, user_id: str | None) -> int:
    """How many successful interactions this user has stored since midnight UTC."""
    # Requests without a user_id are saved with user_id = NULL and share
    # one "anonymous" quota.
    user_filter = (
        Interaction.user_id.is_(None) if user_id is None else Interaction.user_id == user_id
    )
    query = select(func.count(Interaction.id)).where(
        user_filter,
        Interaction.created_at >= _start_of_today_utc(),
        # Only successful requests count. Failed ones (including requests
        # rejected by this quota check) have an error_code and are ignored,
        # so being blocked doesn't use up more quota.
        Interaction.error_code.is_(None),
    )
    return db.scalar(query) or 0


def check_daily_quota(db: Session, user_id: str | None, limit: int | None = None) -> None:
    """Raise QuotaExceededError if the user has reached today's limit.

    `limit` defaults to DAILY_QUOTA from .env; passing it explicitly is
    handy in tests.
    """
    limit = get_settings().daily_quota if limit is None else limit
    used = count_requests_today(db, user_id)
    if used >= limit:
        raise QuotaExceededError(user_id, used, limit)
