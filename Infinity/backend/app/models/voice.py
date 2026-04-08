"""
Voice models — Pydantic schemas for request/response/validation.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from app.config import get_settings


# ════════════════════════════════════════════════════════════════
# API requests
# ════════════════════════════════════════════════════════════════

class VoiceEnqueueRequest(BaseModel):
    user_id: str
    audio_url: str
    voice_input_id: str
    input_mode: Literal["quick", "eod"] = "quick"
    audio_size_bytes: Optional[int] = None
    audio_duration_seconds: Optional[float] = None
    audio_mime_type: Optional[str] = None
    idempotency_key: Optional[str] = None

    @field_validator("audio_size_bytes")
    @classmethod
    def validate_size(cls, v):
        if v is not None:
            settings = get_settings()
            if v > settings.MAX_AUDIO_SIZE_BYTES:
                raise ValueError(f"Audio too large: {v} bytes (max {settings.MAX_AUDIO_SIZE_BYTES})")
        return v

    @field_validator("audio_duration_seconds")
    @classmethod
    def validate_duration(cls, v):
        if v is not None:
            settings = get_settings()
            if v > settings.MAX_AUDIO_DURATION_SECONDS:
                raise ValueError(f"Audio too long: {v}s (max {settings.MAX_AUDIO_DURATION_SECONDS}s)")
        return v

    @field_validator("audio_mime_type")
    @classmethod
    def validate_mime(cls, v):
        if v is not None:
            settings = get_settings()
            if v not in settings.ALLOWED_AUDIO_TYPES:
                raise ValueError(f"Unsupported audio format: {v}")
        return v


class ConfirmActionRequest(BaseModel):
    user_id: str
    voice_input_id: str
    action_index: int = Field(ge=0, le=19)
    confirmed: bool
    edited_entities: Optional[dict] = None
    idempotency_key: str


# ════════════════════════════════════════════════════════════════
# Gemini output validation
# ════════════════════════════════════════════════════════════════

class ExtractedAction(BaseModel):
    intent: Literal[
        "schedule_touchpoint", "create_task", "create_business_opportunity",
        "add_lead", "unknown"
    ]
    confidence: float = Field(ge=0, le=1)
    display_summary: str = Field(max_length=150)
    entities: dict
    warnings: list[str] = []

    @field_validator("entities")
    @classmethod
    def validate_entities(cls, v):
        if not isinstance(v, dict):
            raise ValueError("entities must be a dict")
        return v


class ExtractionResult(BaseModel):
    transcript: str
    actions: list[ExtractedAction] = Field(min_length=0, max_length=20)


# ════════════════════════════════════════════════════════════════
# API responses
# ════════════════════════════════════════════════════════════════

class EnqueueResponse(BaseModel):
    voice_input_id: str
    status: str
    message: str


class ConfirmResponse(BaseModel):
    status: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    breakers: dict
    queue_available: int