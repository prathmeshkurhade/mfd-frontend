"""
Circuit Breaker — prevents cascading failures.
CLOSED → (N failures) → OPEN → (cooldown) → HALF_OPEN → (success) → CLOSED
"""

import time
from app.utils.voice_logger import log_event


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                log_event("", "circuit_breaker", "half_open", service=self.name)
                return True
            return False
        return True

    def record_success(self):
        if self.state == "HALF_OPEN":
            log_event("", "circuit_breaker", "recovered", service=self.name)
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            log_event("", "circuit_breaker", "open",
                      service=self.name, failures=self.failure_count)

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
        }