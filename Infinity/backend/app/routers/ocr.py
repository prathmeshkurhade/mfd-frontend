"""
OCR Router — 4 API endpoints for diary page scanning.
Fully independent from voice. Uses ocr_inputs table.

Endpoints:
  POST /ocr/scan           — enqueue diary page for processing
  GET  /ocr/status/{id}    — poll for results
  POST /ocr/confirm        — confirm/discard extracted action
  GET  /ocr/health         — circuit breaker status
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.ocr import (
    OCRScanRequest, OCRConfirmRequest,
    OCRScanResponse, OCRConfirmResponse,
)
from app.services.ocr.queue import process_ocr_job, get_ocr_semaphore_available
from app.services.ocr.gemini_ocr_service import ocr_breaker
from app.services.voice.entity_writer import write_entity  # shared util — intent→table routing
from app.database import supabase_admin as supabase
from app.utils.rate_limiter import RateLimiter
from app.utils.voice_logger import log_event

router = APIRouter()

_rate_limiter: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = RateLimiter(settings.OCR_RATE_LIMIT_REQUESTS, settings.OCR_RATE_LIMIT_WINDOW)
    return _rate_limiter


def _safe_single_query(query):
    """Execute a single-row query safely — returns None if no row found."""
    try:
        result = query.limit(1).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════
# POST /ocr/scan
# ════════════════════════════════════════════════════════════════

@router.post("/scan", response_model=OCRScanResponse)
async def scan_diary_page(req: OCRScanRequest):
    """
    Scan a diary page image. Returns instantly, processes async.

    Flutter flow:
      1. Photograph diary page
      2. Upload to Supabase Storage
      3. Insert row into ocr_inputs (status='pending')
      4. Call this endpoint
      5. Subscribe to Realtime on ocr_inputs row
      6. When status = needs_confirmation → show confirmation cards
    """
    limiter = _get_limiter()
    if not limiter.check(req.user_id):
        raise HTTPException(status_code=429, detail="Rate limited. Try again shortly.")

    # Idempotency check
    if req.idempotency_key:
        existing = _safe_single_query(
            supabase.table("ocr_inputs")
            .select("id, status")
            .eq("id", req.ocr_input_id)
        )
        if existing and existing.get("status") != "pending":
            return OCRScanResponse(
                ocr_input_id=req.ocr_input_id,
                status=existing["status"],
                message="Already processing or completed",
            )

    # Fire background task
    asyncio.create_task(
        process_ocr_job(req.ocr_input_id, req.user_id, req.image_url)
    )

    log_event(f"ocr-{req.ocr_input_id[:8]}", "enqueue", "accepted",
              user_id=req.user_id, mode="ocr_scan")

    return OCRScanResponse(
        ocr_input_id=req.ocr_input_id,
        status="queued",
        message="Processing diary page. Listen for realtime updates.",
    )


# ════════════════════════════════════════════════════════════════
# GET /ocr/status/{ocr_input_id}
# ════════════════════════════════════════════════════════════════

@router.get("/status/{ocr_input_id}")
async def get_ocr_status(ocr_input_id: str, user_id: str):
    """Poll OCR scan status."""
    result = (
        supabase.table("ocr_inputs")
        .select("id, status, transcript, parsed_data, error_message")
        .eq("id", ocr_input_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data or len(result.data) == 0:
        raise HTTPException(status_code=404, detail="OCR scan not found")
    return result.data[0]


# ════════════════════════════════════════════════════════════════
# POST /ocr/confirm
# ════════════════════════════════════════════════════════════════

@router.post("/confirm", response_model=OCRConfirmResponse)
async def confirm_ocr_action(req: OCRConfirmRequest):
    """
    Confirm/edit/discard an OCR-extracted action. Idempotent.
    Per-action tracking — status='done' only when all actions resolved.
    """
    trace_id = f"ocr-confirm-{req.ocr_input_id[:8]}"

    # Fetch OCR input
    ocr_input = _safe_single_query(
        supabase.table("ocr_inputs")
        .select("*")
        .eq("id", req.ocr_input_id)
    )
    if not ocr_input:
        raise HTTPException(status_code=404, detail="OCR scan not found")

    if ocr_input.get("user_id") != req.user_id:
        raise HTTPException(status_code=403, detail="Not your OCR scan")

    parsed = ocr_input.get("parsed_data", {})
    actions = parsed.get("actions", [])
    confirmed_actions = parsed.get("confirmed_actions", {})

    if req.action_index >= len(actions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_index {req.action_index}. Only {len(actions)} actions.",
        )

    idx_key = str(req.action_index)

    # Idempotency: already resolved?
    if idx_key in confirmed_actions:
        existing = confirmed_actions[idx_key]
        if existing == "discarded":
            return OCRConfirmResponse(status="discarded")
        else:
            return OCRConfirmResponse(
                status="already_created",
                entity_type=existing.get("entity_type"),
                entity_id=existing.get("entity_id"),
            )

    # Discard
    if not req.confirmed:
        confirmed_actions[idx_key] = "discarded"
        parsed["confirmed_actions"] = confirmed_actions

        all_resolved = len(confirmed_actions) >= len(actions)
        new_status = "done" if all_resolved else "needs_confirmation"

        supabase.table("ocr_inputs").update({
            "status": new_status,
            "parsed_data": parsed,
            "processed_at": datetime.now().isoformat() if all_resolved else None,
        }).eq("id", req.ocr_input_id).execute()

        log_event(trace_id, "confirm", "discarded", action_index=req.action_index)
        return OCRConfirmResponse(status="discarded")

    action = actions[req.action_index]
    intent = action.get("intent", "unknown")

    if intent == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Cannot confirm 'unknown' intent. Create the entry manually.",
        )

    entities = req.edited_entities or action.get("entities", {})

    # Validate client_id if present
    client_id = entities.get("client_id")
    if client_id:
        client_data = _safe_single_query(
            supabase.table("clients")
            .select("id")
            .eq("id", client_id)
            .eq("user_id", req.user_id)
            .eq("is_deleted", False)
        )
        if not client_data:
            raise HTTPException(status_code=400, detail=f"Client {client_id} not found or deleted")

    # Write entity (reuses voice entity_writer — it's just intent→table routing)
    try:
        entity_type, entity_id = write_entity(
            intent=intent,
            user_id=req.user_id,
            entities=entities,
            trace_id=trace_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log_event(trace_id, "confirm", "write_failed", error=str(e)[:200])
        raise HTTPException(status_code=500, detail=f"Failed to create entity: {e}")

    # Track this action
    confirmed_actions[idx_key] = {"entity_type": entity_type, "entity_id": entity_id}
    parsed["confirmed_actions"] = confirmed_actions

    all_resolved = len(confirmed_actions) >= len(actions)
    new_status = "done" if all_resolved else "needs_confirmation"

    supabase.table("ocr_inputs").update({
        "status": new_status,
        "parsed_data": parsed,
        "processed_at": datetime.now().isoformat() if all_resolved else None,
        "created_entity_type": entity_type,
        "created_entity_id": entity_id,
    }).eq("id", req.ocr_input_id).execute()

    log_event(trace_id, "confirm", "created",
              action_index=req.action_index,
              entity_type=entity_type, entity_id=entity_id,
              resolved=f"{len(confirmed_actions)}/{len(actions)}")

    return OCRConfirmResponse(
        status="created",
        entity_type=entity_type,
        entity_id=entity_id,
    )


# ════════════════════════════════════════════════════════════════
# GET /ocr/health
# ════════════════════════════════════════════════════════════════

@router.get("/health")
async def ocr_health():
    """OCR pipeline health — circuit breaker + queue capacity."""
    return {
        "status": "ok",
        "breakers": {
            "ocr_gemini": ocr_breaker.to_dict(),
        },
        "queue_available": get_ocr_semaphore_available(),
    }