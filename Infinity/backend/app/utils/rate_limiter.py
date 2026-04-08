"""
Rate Limiter — sliding window, per-user.
In-memory for single instance. Swap to Redis for multi-instance.
"""

import time


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check(self, user_id: str) -> bool:
        now = time.time()
        cutoff = now - self.window_seconds
        entries = self._requests.get(user_id, [])
        entries = [t for t in entries if t > cutoff]
        self._requests[user_id] = entries

        if len(entries) >= self.max_requests:
            return False
        entries.append(now)
        return True

    def remaining(self, user_id: str) -> int:
        now = time.time()
        cutoff = now - self.window_seconds
        active = [t for t in self._requests.get(user_id, []) if t > cutoff]
        return max(0, self.max_requests - len(active))