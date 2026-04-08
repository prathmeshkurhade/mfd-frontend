from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WebhookPayload(BaseModel):
    source: str  # whatsapp_notif, whatsapp_input, email_service
    event_type: str  # delivery_status, message_received, form_submission
    payload: Dict[str, Any]
    timestamp: Optional[datetime] = None


class WebhookLogResponse(BaseModel):
    id: UUID
    source: str
    event_type: str
    payload: Dict[str, Any]
    processed: bool = False
    processed_at: Optional[datetime] = None
    processing_result: Optional[Dict[str, Any]] = None
    related_user_id: Optional[UUID] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookLogListResponse(BaseModel):
    logs: List[WebhookLogResponse]
    total: int


class DeliveryStatusPayload(BaseModel):
    message_id: str
    status: str  # sent, delivered, read, failed
    timestamp: datetime
    error: Optional[str] = None


class WhatsAppMessagePayload(BaseModel):
    from_number: str
    message_type: str  # text, voice, image
    content: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: datetime
