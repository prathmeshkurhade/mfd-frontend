"""
Voice Router — 4 API endpoints.
Thin layer: validate → delegate → respond. No business logic here.
"""

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.models.voice import (
    VoiceEnqueueRequest, ConfirmActionRequest,
    EnqueueResponse, ConfirmResponse, HealthResponse,
)
from app.constants.enums import IntentType, VoiceInputStatus
from app.services.voice.queue import process_voice_job, get_semaphore_available
from app.services.voice.entity_writer import write_entity
from app.services.voice.gemini_service import gemini_breaker
from app.services.voice.fallback import sarvam_breaker, claude_breaker
from app.database import supabase
from app.utils.rate_limiter import RateLimiter
from app.utils.voice_logger import log_event
from app.database import supabase_admin as supabase
router = APIRouter()

_rate_limiter: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = RateLimiter(settings.VOICE_RATE_LIMIT_REQUESTS, settings.VOICE_RATE_LIMIT_WINDOW)
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
# POST /voice/enqueue
# ════════════════════════════════════════════════════════════════

@router.post("/enqueue", response_model=EnqueueResponse)
async def enqueue_voice(req: VoiceEnqueueRequest):
    """Accept voice input, process async. Returns in ~100ms."""
    limiter = _get_limiter()
    if not limiter.check(req.user_id):
        raise HTTPException(status_code=429, detail="Rate limited. Try again shortly.")

    # Idempotency check
    if req.idempotency_key:
        existing = _safe_single_query(
            supabase.table("voice_inputs")
            .select("id, status")
            .eq("id", req.voice_input_id)
        )
        if existing and existing.get("status") != VoiceInputStatus.PENDING.value:
            return EnqueueResponse(
                voice_input_id=req.voice_input_id,
                status=existing["status"],
                message="Already processing or completed",
            )

    asyncio.create_task(
        process_voice_job(req.voice_input_id, req.user_id, req.audio_url, req.input_mode)
    )

    log_event(f"voice-{req.voice_input_id[:8]}", "enqueue", "accepted",
              user_id=req.user_id, mode=req.input_mode)

    return EnqueueResponse(
        voice_input_id=req.voice_input_id,
        status="queued",
        message="Processing started. Listen for realtime updates.",
    )


# ════════════════════════════════════════════════════════════════
# POST /voice/confirm
# ════════════════════════════════════════════════════════════════

@router.post("/confirm", response_model=ConfirmResponse)
async def confirm_action(req: ConfirmActionRequest):
    """
    User confirms/edits/discards a parsed action. Idempotent.
    Each action is confirmed independently by action_index.
    Status becomes 'done' only when every action is confirmed or discarded.
    """
    trace_id = f"confirm-{req.voice_input_id[:8]}"

    # Fetch voice input
    voice_input = _safe_single_query(
        supabase.table("voice_inputs")
        .select("*")
        .eq("id", req.voice_input_id)
    )
    if not voice_input:
        raise HTTPException(status_code=404, detail="Voice input not found")

    if voice_input.get("user_id") != req.user_id:
        raise HTTPException(status_code=403, detail="Not your voice input")

    parsed = voice_input.get("parsed_data", {})
    actions = parsed.get("actions", [])
    confirmed_actions = parsed.get("confirmed_actions", {})

    if req.action_index >= len(actions):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action_index {req.action_index}. Only {len(actions)} actions.",
        )

    idx_key = str(req.action_index)

    # Idempotency: this specific action already resolved?
    if idx_key in confirmed_actions:
        existing = confirmed_actions[idx_key]
        if existing == "discarded":
            return ConfirmResponse(status="discarded")
        else:
            return ConfirmResponse(
                status="already_created",
                entity_type=existing.get("entity_type"),
                entity_id=existing.get("entity_id"),
            )

    # Discard
    if not req.confirmed:
        confirmed_actions[idx_key] = "discarded"
        parsed["confirmed_actions"] = confirmed_actions

        all_resolved = len(confirmed_actions) >= len(actions)
        new_status = VoiceInputStatus.DONE.value if all_resolved else VoiceInputStatus.NEEDS_CONFIRMATION.value

        supabase.table("voice_inputs").update({
            "status": new_status,
            "parsed_data": parsed,
            "processed_at": datetime.now().isoformat() if all_resolved else None,
        }).eq("id", req.voice_input_id).execute()

        log_event(trace_id, "confirm", "discarded", action_index=req.action_index)
        return ConfirmResponse(status="discarded")

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

    # Write entity
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
    new_status = VoiceInputStatus.DONE.value if all_resolved else VoiceInputStatus.NEEDS_CONFIRMATION.value

    supabase.table("voice_inputs").update({
        "status": new_status,
        "parsed_data": parsed,
        "processed_at": datetime.now().isoformat() if all_resolved else None,
        "created_entity_type": entity_type,
        "created_entity_id": entity_id,
    }).eq("id", req.voice_input_id).execute()

    log_event(trace_id, "confirm", "created",
              action_index=req.action_index,
              entity_type=entity_type, entity_id=entity_id,
              resolved=f"{len(confirmed_actions)}/{len(actions)}")

    return ConfirmResponse(
        status="created",
        entity_type=entity_type,
        entity_id=entity_id,
    )


# ════════════════════════════════════════════════════════════════
# GET /voice/status/{voice_input_id}
# ════════════════════════════════════════════════════════════════

@router.get("/status/{voice_input_id}")
async def get_voice_status(voice_input_id: str, user_id: str):
    """Polling fallback if Supabase Realtime drops."""
    data = _safe_single_query(
        supabase.table("voice_inputs")
        .select("id, status, transcript, parsed_data, error_message, input_mode")
        .eq("id", voice_input_id)
        .eq("user_id", user_id)
    )
    if not data:
        raise HTTPException(status_code=404, detail="Voice input not found")
    return data


# ════════════════════════════════════════════════════════════════
# GET /voice/health
# ════════════════════════════════════════════════════════════════

@router.get("/health", response_model=HealthResponse)
async def voice_health():
    """Circuit breaker states + queue capacity."""
    return HealthResponse(
        status="ok",
        breakers={
            "gemini": gemini_breaker.to_dict(),
            "sarvam": sarvam_breaker.to_dict(),
            "claude": claude_breaker.to_dict(),
        },
        queue_available=get_semaphore_available(),
    )