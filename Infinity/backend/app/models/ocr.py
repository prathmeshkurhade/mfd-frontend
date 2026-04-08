"""
OCR Models — Pydantic schemas for diary page scanning.
Fully independent from voice models.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ════════════════════════════════════════════════════════════════
# API Requests
# ════════════════════════════════════════════════════════════════

class OCRScanRequest(BaseModel):
    user_id: str
    image_url: str
    ocr_input_id: str
    image_size_bytes: Optional[int] = None
    image_mime_type: Optional[str] = None
    idempotency_key: Optional[str] = None


class OCRConfirmRequest(BaseModel):
    user_id: str
    ocr_input_id: str
    action_index: int = Field(ge=0, le=19)
    confirmed: bool
    edited_entities: Optional[dict] = None
    idempotency_key: str


# ════════════════════════════════════════════════════════════════
# Gemini output validation (same structure, independent classes)
# ════════════════════════════════════════════════════════════════

class OCRExtractedAction(BaseModel):
    """Validates a single action from Gemini's JSON output."""
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


class OCRExtractionResult(BaseModel):
    """Top-level wrapper for Gemini's full OCR response."""
    transcript: str
    actions: list[OCRExtractedAction] = Field(min_length=0, max_length=50)


# ════════════════════════════════════════════════════════════════
# API Responses
# ════════════════════════════════════════════════════════════════

class OCRScanResponse(BaseModel):
    ocr_input_id: str
    status: str
    message: str


class OCRConfirmResponse(BaseModel):
    status: str  # created | discarded | already_created
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None