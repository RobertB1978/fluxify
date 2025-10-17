from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(tz=timezone.utc)
