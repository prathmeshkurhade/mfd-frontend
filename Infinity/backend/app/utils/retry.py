"""
Retry — exponential backoff with jitter.
Transient errors (timeout, 429, 5xx) → retry.
Permanent errors (400, 401, 403, 404) → fail fast.
"""

import asyncio
import random
from typing import Optional, Callable, Awaitable, TypeVar

import httpx
from fastapi import HTTPException

from app.utils.circuit_breaker import CircuitBreaker
from app.utils.voice_logger import log_event

T = TypeVar("T")
PERMANENT_CODES = {400, 401, 403, 404, 405, 422}


async def retry_async(
    func: Callable[[], Awaitable[T]],
    *,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    breaker: Optional[CircuitBreaker] = None,
    trace_id: str = "",
    stage: str = "",
) -> T:
    last_exc: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        if breaker and not breaker.can_execute():
            log_event(trace_id, stage, "circuit_open", service=breaker.name)
            raise HTTPException(status_code=503, detail=f"{breaker.name} temporarily unavailable")

        try:
            result = await func()
            if breaker:
                breaker.record_success()
            return result

        except httpx.TimeoutException as e:
            last_exc = e
            if breaker:
                breaker.record_failure()
            log_event(trace_id, stage, "timeout", attempt=attempt)

        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            if code in PERMANENT_CODES:
                log_event(trace_id, stage, "permanent_error", status=code)
                raise
            last_exc = e
            if breaker:
                breaker.record_failure()
            log_event(trace_id, stage, "transient_error", status=code, attempt=attempt)

        except ValueError as e:
            last_exc = e
            log_event(trace_id, stage, "value_error", attempt=attempt, error=str(e)[:200])

        except Exception as e:
            last_exc = e
            if breaker:
                breaker.record_failure()
            log_event(trace_id, stage, "unexpected_error", attempt=attempt, error=str(e)[:200])

        if attempt < max_retries:
            delay = min(base_delay * (2 ** attempt), max_delay)
            delay *= 0.75 + random.random() * 0.5
            log_event(trace_id, stage, "retrying", attempt=attempt + 1, delay_s=round(delay, 2))
            await asyncio.sleep(delay)

    log_event(trace_id, stage, "exhausted_retries", max_retries=max_retries)
    raise last_exc or HTTPException(status_code=500, detail=f"{stage}: max retries exhausted")