from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageTemplateCreate(BaseModel):
    template_type: str
    channel: str  # email, whatsapp
    name: str = Field(..., max_length=255)
    subject: Optional[str] = None  # for email
    content: str


class MessageTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    subject: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class MessageTemplateResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    template_type: str
    channel: str
    name: str
    subject: Optional[str] = None
    content: str
    is_active: bool = True
    is_system: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageTemplateListResponse(BaseModel):
    templates: List[MessageTemplateResponse]
    total: int


class RenderTemplateRequest(BaseModel):
    template_id: UUID
    variables: Dict[str, Any]  # {mfd_name: "Rahul", client_name: "Amit", ...}


class RenderTemplateResponse(BaseModel):
    rendered_content: str
    rendered_subject: Optional[str] = None
