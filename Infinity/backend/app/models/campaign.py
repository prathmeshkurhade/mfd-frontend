from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CampaignCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    message_template: Optional[str] = None
    channel: Optional[str] = None
    scheduled_date: Optional[date] = None
    client_ids: List[UUID] = []
    filters: Optional[Dict[str, Any]] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    message_template: Optional[str] = None
    channel: Optional[str] = None
    scheduled_date: Optional[date] = None
    client_ids: Optional[List[UUID]] = None
    filters: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    message_template: Optional[str] = None
    channel: Optional[str] = None
    scheduled_date: Optional[date] = None
    is_executed: bool = False
    executed_at: Optional[datetime] = None
    total_recipients: int = 0
    successful_sends: int = 0
    failed_sends: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class CampaignExecuteResponse(BaseModel):
    campaign_id: UUID
    total_recipients: int
    successful: int
    failed: int
    message: str
