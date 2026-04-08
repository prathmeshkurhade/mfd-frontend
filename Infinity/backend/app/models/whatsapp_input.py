from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WhatsAppDataInputResponse(BaseModel):
    id: UUID
    user_id: UUID
    input_type: str
    raw_message: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    voice_note_url: Optional[str] = None
    transcription: Optional[str] = None
    status: str
    processed_at: Optional[datetime] = None
    created_entity_type: Optional[str] = None
    created_entity_id: Optional[UUID] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WhatsAppDataInputListResponse(BaseModel):
    inputs: List[WhatsAppDataInputResponse]
    total: int


class ProcessInputResponse(BaseModel):
    success: bool
    input_id: UUID
    created_entity_type: Optional[str] = None
    created_entity_id: Optional[UUID] = None
    message: str


class VoiceNoteInput(BaseModel):
    user_phone: str
    audio_url: str
    duration_seconds: Optional[int] = None


class TextCommandInput(BaseModel):
    user_phone: str
    command: str
    parameters: Optional[Dict[str, Any]] = None
