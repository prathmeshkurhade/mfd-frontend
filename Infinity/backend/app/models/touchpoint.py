from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import (
    BOOutcomeType,
    InteractionType,
    OpportunityType,
    TouchpointStatusType,
)


class TouchpointCreate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    interaction_type: InteractionType
    scheduled_date: date
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: TouchpointStatusType = TouchpointStatusType.scheduled


class TouchpointUpdate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    interaction_type: Optional[InteractionType] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[TouchpointStatusType] = None
    mom_text: Optional[str] = None


class TouchpointResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    client_name: Optional[str] = None
    lead_name: Optional[str] = None
    interaction_type: InteractionType
    scheduled_date: date
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: TouchpointStatusType
    completed_at: Optional[datetime] = None
    mom_text: Optional[str] = None
    mom_pdf_url: Optional[str] = None
    mom_audio_url: Optional[str] = None
    mom_sent_to_client: Optional[bool] = None
    mom_sent_at: Optional[datetime] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TouchpointListResponse(BaseModel):
    touchpoints: List[TouchpointResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class TouchpointComplete(BaseModel):
    actual_date: Optional[date] = None
    actual_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    mom_text: Optional[str] = None
    outcome: Optional[BOOutcomeType] = None
    create_follow_up_task: bool = False
    follow_up_task_title: Optional[str] = None
    follow_up_task_date: Optional[date] = None
    create_business_opportunity: bool = False
    opportunity_type: Optional[OpportunityType] = None
    opportunity_amount: Optional[float] = Field(None, ge=0)


class MOMUpdate(BaseModel):
    mom_text: str


class MOMResponse(BaseModel):
    touchpoint_id: UUID
    mom_text: Optional[str] = None
    mom_pdf_url: Optional[str] = None


class ClientTouchpointStats(BaseModel):
    client_id: UUID
    total_touchpoints: int
    completed_touchpoints: int
    this_year_count: int
    last_touchpoint_date: Optional[date] = None
    touchpoints: List[TouchpointResponse]
