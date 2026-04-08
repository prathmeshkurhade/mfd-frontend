"""
Queue Service — background job processor.

Flow:
  1. Semaphore gate (max N concurrent)
  2. Try Gemini (primary)
  3. If Gemini fails → try Sarvam + Claude (fallback)
  4. If both fail → degrade to "unknown" intent
  5. If total failure → mark as failed
"""

import asyncio
import time
from datetime import datetime

from app.config import get_settings
from app.services.voice.gemini_service import gemini_breaker
from app.services.voice.fallback import sarvam_breaker, claude_breaker
from app.models.voice import ExtractionResult, ExtractedAction
from app.constants.enums import VoiceInputStatus
from app.database import supabase
from app.utils.voice_logger import log_event
from app.database import supabase_admin as supabase
_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(get_settings().MAX_CONCURRENT_VOICE_JOBS)
    return _semaphore


def get_semaphore_available() -> int:
    sem = _get_semaphore()
    return sem._value


def _make_degraded_result(transcript: str = "") -> dict:
    return ExtractionResult(
        transcript=transcript or "Transcription unavailable",
        actions=[
            ExtractedAction(
                intent="unknown",
                confidence=0.0,
                display_summary="Could not parse — please create manually",
                entities={"raw_transcript": transcript} if transcript else {},
                warnings=["Automatic extraction failed. Create the entry manually from the transcript."],
            )
        ],
    ).model_dump(mode="json")


async def process_voice_job(
    voice_input_id: str,
    user_id: str,
    audio_url: str,
    input_mode: str,
):
    trace_id = f"voice-{voice_input_id[:8]}"
    start_time = time.time()
    settings = get_settings()
    sem = _get_semaphore()

    async with sem:
        try:
            supabase.table("voice_inputs").update({
                "status": VoiceInputStatus.PROCESSING.value,
                "trace_id": trace_id,
            }).eq("id", voice_input_id).execute()

            log_event(trace_id, "job", "started", user_id=user_id, mode=input_mode)

            clients_result = (
                supabase.table("clients")
                .select("id, name, phone, area, total_aum")
                .eq("user_id", user_id)
                .eq("is_deleted", False)
                .order("updated_at", desc=True)
                .limit(settings.MAX_CLIENTS_IN_PROMPT)
                .execute()
            )
            user_clients = clients_result.data or []

            extraction = None
            try:
                from app.services.voice.gemini_service import process_audio
                t1 = time.time()
                extraction = await process_audio(audio_url, user_clients, trace_id)
                log_event(trace_id, "gemini", "complete",
                          duration_ms=round((time.time() - t1) * 1000))

            except Exception as gemini_err:
                log_event(trace_id, "gemini", "failed", error=str(gemini_err)[:300])

                try:
                    from app.services.voice.fallback import process_fallback
                    t2 = time.time()
                    extraction = await process_fallback(audio_url, user_clients, trace_id)
                    log_event(trace_id, "fallback", "complete",
                              duration_ms=round((time.time() - t2) * 1000))

                except Exception as fallback_err:
                    log_event(trace_id, "fallback", "failed",
                              error=str(fallback_err)[:300])

                    degraded_data = _make_degraded_result()

                    supabase.table("voice_inputs").update({
                        "status": VoiceInputStatus.NEEDS_CONFIRMATION.value,
                        "parsed_data": degraded_data,
                        "error_message": f"Gemini: {str(gemini_err)[:200]}; Fallback: {str(fallback_err)[:200]}",
                    }).eq("id", voice_input_id).execute()

                    total_ms = round((time.time() - start_time) * 1000)
                    log_event(trace_id, "job", "degraded", total_duration_ms=total_ms)
                    return

            supabase.table("voice_inputs").update({
                "status": VoiceInputStatus.NEEDS_CONFIRMATION.value,
                "transcript": extraction.transcript,
                "parsed_data": extraction.model_dump(mode="json"),
            }).eq("id", voice_input_id).execute()

            total_ms = round((time.time() - start_time) * 1000)
            log_event(trace_id, "job", "complete",
                      total_duration_ms=total_ms,
                      num_actions=len(extraction.actions))

        except Exception as e:
            total_ms = round((time.time() - start_time) * 1000)
            log_event(trace_id, "job", "failed",
                      error=str(e)[:500], total_duration_ms=total_ms)

            try:
                supabase.table("voice_inputs").update({
                    "status": VoiceInputStatus.FAILED.value,
                    "error_message": str(e)[:500],
                }).eq("id", voice_input_id).execute()
            except Exception:
                pass