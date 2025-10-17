from __future__ import annotations

from collections import defaultdict, deque
from time import monotonic
from typing import Callable, Deque, DefaultDict

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from ...config import settings
from ...database import SessionLocal


_rate_limiters: DefaultDict[str, Deque[float]] = defaultdict(deque)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def rate_limiter(request: Request) -> None:
    identifier = request.client.host if request.client else "anonymous"
    limit = settings.rate_limit_requests
    window = settings.rate_limit_window_seconds
    now = monotonic()
    bucket = _rate_limiters[identifier]

    while bucket and now - bucket[0] > window:
        bucket.popleft()

    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )

    bucket.append(now)


def get_rate_limiter_dependency() -> Callable[[Request], None]:
    return rate_limiter
