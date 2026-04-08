"""
OCR Queue — background job processor for diary page scanning.
Independent from voice queue. Uses ocr_inputs table.
"""

import asyncio
import time

from app.config import get_settings
from app.models.ocr import OCRExtractionResult, OCRExtractedAction
from app.database import supabase_admin as supabase
from app.utils.voice_logger import log_event

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(get_settings().MAX_CONCURRENT_OCR_JOBS)
    return _semaphore


def get_ocr_semaphore_available() -> int:
    sem = _get_semaphore()
    return sem._value


def _make_degraded_result(ocr_text: str = "") -> dict:
    """When extraction fails, return 'unknown' intent."""
    return OCRExtractionResult(
        transcript=ocr_text or "OCR extraction unavailable",
        actions=[
            OCRExtractedAction(
                intent="unknown",
                confidence=0.0,
                display_summary="Could not parse diary page — create manually",
                entities={"raw_text": ocr_text} if ocr_text else {},
                warnings=["Automatic extraction failed. Create entries manually."],
            )
        ],
    ).model_dump(mode="json")


async def process_ocr_job(
    ocr_input_id: str,
    user_id: str,
    image_url: str,
):
    """
    Process one diary page scan. Runs as async background task.
    Writes to ocr_inputs table (NOT voice_inputs).
    """
    trace_id = f"ocr-{ocr_input_id[:8]}"
    start_time = time.time()
    settings = get_settings()
    sem = _get_semaphore()

    async with sem:
        try:
            # Status: processing
            supabase.table("ocr_inputs").update({
                "status": "processing",
                "trace_id": trace_id,
            }).eq("id", ocr_input_id).execute()

            log_event(trace_id, "job", "started", user_id=user_id, mode="ocr_scan")

            # Fetch client list
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

            # Call Gemini Vision
            extraction = None
            try:
                from app.services.ocr.gemini_ocr_service import process_image
                t1 = time.time()
                extraction = await process_image(image_url, user_clients, trace_id)
                log_event(trace_id, "ocr_gemini", "complete",
                          duration_ms=round((time.time() - t1) * 1000))

            except Exception as gemini_err:
                log_event(trace_id, "ocr_gemini", "failed", error=str(gemini_err)[:300])

                # Graceful degradation
                degraded_data = _make_degraded_result()
                supabase.table("ocr_inputs").update({
                    "status": "needs_confirmation",
                    "parsed_data": degraded_data,
                    "error_message": f"OCR Gemini: {str(gemini_err)[:400]}",
                }).eq("id", ocr_input_id).execute()

                total_ms = round((time.time() - start_time) * 1000)
                log_event(trace_id, "job", "degraded", total_duration_ms=total_ms)
                return

            # Success: update row → triggers Realtime
            supabase.table("ocr_inputs").update({
                "status": "needs_confirmation",
                "transcript": extraction.transcript,
                "parsed_data": extraction.model_dump(mode="json"),
            }).eq("id", ocr_input_id).execute()

            total_ms = round((time.time() - start_time) * 1000)
            log_event(trace_id, "job", "complete",
                      total_duration_ms=total_ms,
                      num_actions=len(extraction.actions))

        except Exception as e:
            total_ms = round((time.time() - start_time) * 1000)
            log_event(trace_id, "job", "failed",
                      error=str(e)[:500], total_duration_ms=total_ms)
            try:
                supabase.table("ocr_inputs").update({
                    "status": "failed",
                    "error_message": str(e)[:500],
                }).eq("id", ocr_input_id).execute()
            except Exception:
                pass