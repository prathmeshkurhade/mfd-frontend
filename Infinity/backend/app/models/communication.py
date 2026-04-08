"""
Communication Models
[TEAM] - WhatsApp & Email implementation by other intern
These schemas define the interface only
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


# ==================== WHATSAPP [TEAM] ====================
class WhatsAppMessageRequest(BaseModel):
    client_id: UUID
    message: str
    template_id: Optional[str] = None


class WhatsAppDocumentRequest(BaseModel):
    client_id: UUID
    document_id: UUID
    message: Optional[str] = None


class WhatsAppMessageResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str
    note: Optional[str] = None


class WhatsAppTemplate(BaseModel):
    id: str
    name: str
    content: str


class WhatsAppTemplatesResponse(BaseModel):
    templates: List[WhatsAppTemplate]


# ==================== EMAIL [TEAM] ====================
class EmailRequest(BaseModel):
    client_id: UUID
    subject: str
    body: str
    attachment_ids: List[UUID] = []


class EmailResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str


# ==================== COMMUNICATION LOG ====================
class CommunicationLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: UUID
    channel: str
    message_type: str
    content: Optional[str] = None
    status: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CommunicationHistoryResponse(BaseModel):
    logs: List[CommunicationLogResponse]
    total: int
