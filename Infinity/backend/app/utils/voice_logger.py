"""
Structured JSON logger with trace IDs.
Filter trace_id=voice-abc12345 to see a complete pipeline trace.
"""

import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log.update(record.extra_data)
        return json.dumps(log, default=str)


_logger: logging.Logger | None = None


def _get_logger() -> logging.Logger:
    global _logger
    if _logger is None:
        _logger = logging.getLogger("voice_workflow")
        if not _logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(JSONFormatter())
            _logger.addHandler(handler)
            _logger.setLevel(logging.INFO)
    return _logger


def log_event(trace_id: str, stage: str, status: str, **kwargs):
    _get_logger().info(
        f"{stage}:{status}",
        extra={"extra_data": {"trace_id": trace_id, "stage": stage, "status": status, **kwargs}},
    )