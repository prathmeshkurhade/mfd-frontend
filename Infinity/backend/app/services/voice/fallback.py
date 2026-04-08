"""
Fallback Service — Sarvam STT + Claude Haiku.

Only activated when Gemini's circuit breaker trips.
"""

import json
import httpx


from app.config import get_settings
from app.models.voice import ExtractionResult
from app.prompts.intent_extraction import SYSTEM_PROMPT, build_prompt_context
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.retry import retry_async
from app.utils.voice_logger import log_event

sarvam_breaker = CircuitBreaker("sarvam", failure_threshold=5, recovery_timeout=60)
claude_breaker = CircuitBreaker("claude", failure_threshold=3, recovery_timeout=30)




async def _download_audio(audio_url: str, trace_id: str) -> bytes:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        return resp.content




