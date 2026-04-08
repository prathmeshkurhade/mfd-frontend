from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUpload(BaseModel):
    client_id: UUID
    name: str = Field(..., max_length=255)
    document_type: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None


class DocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: UUID
    name: str
    document_type: Optional[str] = None
    file_url: str
    drive_file_id: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    shared_with_client: bool = False
    shared_at: Optional[datetime] = None
    shared_via: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class DocumentShareRequest(BaseModel):
    document_id: UUID
    share_via: str  # whatsapp or email
    message: Optional[str] = None


class DocumentShareResponse(BaseModel):
    message: str
    shared_at: datetime
