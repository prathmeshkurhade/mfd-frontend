"""
Gemini OCR Service — image → structured actions.

Independent from voice pipeline. Uses same Gemini API key but
separate circuit breaker, separate prompt, separate models.
"""

import json
import httpx
from google import genai
from google.genai import types

from app.config import get_settings
from app.models.ocr import OCRExtractionResult
from app.prompts.ocr_extraction import OCR_SYSTEM_PROMPT, build_ocr_context
from app.utils.circuit_breaker import CircuitBreaker
from app.utils.retry import retry_async
from app.utils.voice_logger import log_event

ocr_breaker = CircuitBreaker("ocr_gemini", failure_threshold=5, recovery_timeout=60)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


async def _download_image(image_url: str, trace_id: str) -> tuple[bytes, str]:
    """Download image from Supabase Storage. Returns (bytes, mime_type)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/jpeg")

        if "png" in content_type:
            mime = "image/png"
        elif "webp" in content_type:
            mime = "image/webp"
        elif "bmp" in content_type:
            mime = "image/bmp"
        elif "tiff" in content_type:
            mime = "image/tiff"
        else:
            mime = "image/jpeg"

        log_event(trace_id, "image_download", "success",
                  size_kb=round(len(resp.content) / 1024, 1), mime=mime)
        return resp.content, mime


async def process_image(
    image_url: str,
    user_clients: list[dict],
    trace_id: str,
) -> OCRExtractionResult:
    """
    Image in → validated OCRExtractionResult out.
    """
    settings = get_settings()
    client = _get_client()

    # Step 1: Download image
    image_bytes, mime_type = await _download_image(image_url, trace_id)

    # Step 2: Build context
    context_text = build_ocr_context(
        user_clients=user_clients,
        max_clients=settings.MAX_CLIENTS_IN_PROMPT,
    )

    # Step 3: Call Gemini Vision with retry + circuit breaker
    async def _call() -> OCRExtractionResult:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=context_text),
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type,
                        ),
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=OCR_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )

        raw_text = response.text.strip()
        clean = raw_text.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError as e:
            log_event(trace_id, "ocr_gemini", "json_parse_failed", raw_preview=raw_text[:300])
            raise ValueError(f"Gemini returned invalid JSON: {e}")

        try:
            result = OCRExtractionResult(**parsed)
        except Exception as e:
            log_event(trace_id, "ocr_gemini", "schema_failed", error=str(e)[:300])
            raise ValueError(f"Schema validation failed: {e}")

        return result

    try:
        result = await retry_async(
            _call,
            max_retries=settings.MAX_RETRIES,
            base_delay=settings.RETRY_BASE_DELAY,
            max_delay=settings.RETRY_MAX_DELAY,
            breaker=ocr_breaker,
            trace_id=trace_id,
            stage="ocr_gemini",
        )
        log_event(trace_id, "ocr_gemini", "success",
                  num_actions=len(result.actions),
                  transcript_len=len(result.transcript))
        return result

    except Exception as e:
        log_event(trace_id, "ocr_gemini", "failed", error=str(e)[:300])
        raise