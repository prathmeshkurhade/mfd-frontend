"""
Gemini Service — the heart of the pipeline.

One API call does everything:
  - Understands Hindi/English/Marathi audio natively (no STT step)
  - Extracts structured actions with entities
  - Returns transcript + JSON

Uses the NEW google-genai SDK (not the deprecated google-generativeai).
"""

import json
import httpx
from google import genai
from google.genai import types

from app.config import get_settings
from app.models.voice import ExtractionResult
from app.prompts.intent_extraction import SYSTEM_PROMPT, build_prompt_context
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.retry import retry_async
from app.utils.voice_logger import log_event

gemini_breaker = CircuitBreaker("gemini", failure_threshold=5, recovery_timeout=60)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def _download_audio(audio_url: str, trace_id: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(audio_url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "audio/ogg")

        if "ogg" in content_type or "opus" in content_type:
            mime = "audio/ogg"
        elif "wav" in content_type:
            mime = "audio/wav"
        elif "mp3" in content_type or "mpeg" in content_type:
            mime = "audio/mp3"
        elif "webm" in content_type:
            mime = "audio/webm"
        elif "mp4" in content_type or "m4a" in content_type:
            mime = "audio/mp4"
        else:
            mime = "audio/ogg"

        log_event(trace_id, "audio_download", "success",
                  size_kb=round(len(resp.content) / 1024, 1), mime=mime)
        return resp.content, mime


async def process_audio(
    audio_url: str,
    user_clients: list[dict],
    trace_id: str,
) -> ExtractionResult:
    settings = get_settings()
    client = _get_client()

    audio_bytes, mime_type = await _download_audio(audio_url, trace_id)

    context_text = build_prompt_context(
        user_clients=user_clients,
        max_clients=settings.MAX_CLIENTS_IN_PROMPT,
    )

    async def _call() -> ExtractionResult:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=context_text),
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=mime_type,
                        ),
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_text = response.text.strip()
        clean = raw_text.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError as e:
            log_event(trace_id, "gemini", "json_parse_failed", raw_preview=raw_text[:300])
            raise ValueError(f"Gemini returned invalid JSON: {e}")

        try:
            result = ExtractionResult(**parsed)
        except Exception as e:
            log_event(trace_id, "gemini", "schema_failed", error=str(e)[:300])
            raise ValueError(f"Schema validation failed: {e}")

        return result

    try:
        result = await retry_async(
            _call,
            max_retries=settings.MAX_RETRIES,
            base_delay=settings.RETRY_BASE_DELAY,
            max_delay=settings.RETRY_MAX_DELAY,
            breaker=gemini_breaker,
            trace_id=trace_id,
            stage="gemini_audio",
        )
        log_event(trace_id, "gemini", "success",
                  num_actions=len(result.actions),
                  transcript_len=len(result.transcript))
        return result

    except Exception as e:
        log_event(trace_id, "gemini", "failed", error=str(e)[:300])
        raise