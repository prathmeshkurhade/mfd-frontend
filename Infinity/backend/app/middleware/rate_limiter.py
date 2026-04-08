"""
In-memory rate limiter using a sliding window approach.

No external dependencies (no Redis needed). Suitable for single-instance
deployments. For multi-instance, swap the store for Redis.
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Optional

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class _TokenBucket:
    """Simple token-bucket implementation per key."""

    __slots__ = ("capacity", "refill_rate", "tokens", "last_refill")

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

    @property
    def retry_after(self) -> float:
        if self.tokens >= 1:
            return 0
        return (1 - self.tokens) / self.refill_rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP rate limiter.

    Args:
        app: ASGI application
        requests_per_minute: max requests allowed per minute per IP
        auth_requests_per_minute: stricter limit for auth endpoints (login/signup)
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        auth_requests_per_minute: int = 10,
    ):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.auth_rpm = auth_requests_per_minute
        self._buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(self.rpm, self.rpm / 60.0)
        )
        self._auth_buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(self.auth_rpm, self.auth_rpm / 60.0)
        )
        self._lock = Lock()
        self._last_cleanup = time.monotonic()

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_auth_path(self, path: str) -> bool:
        return "/auth/login" in path or "/auth/signup" in path

    def _cleanup_stale_buckets(self):
        """Remove buckets that haven't been used in 5 minutes."""
        now = time.monotonic()
        if now - self._last_cleanup < 300:
            return
        self._last_cleanup = now
        stale_threshold = now - 300
        for store in (self._buckets, self._auth_buckets):
            stale_keys = [
                k for k, v in store.items() if v.last_refill < stale_threshold
            ]
            for k in stale_keys:
                del store[k]

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = self._get_client_ip(request)
        is_auth = self._is_auth_path(request.url.path)

        with self._lock:
            self._cleanup_stale_buckets()
            bucket = self._auth_buckets[client_ip] if is_auth else self._buckets[client_ip]
            allowed = bucket.consume()
            retry_after = bucket.retry_after

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after_seconds": round(retry_after, 1),
                },
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        response = await call_next(request)
        return response
