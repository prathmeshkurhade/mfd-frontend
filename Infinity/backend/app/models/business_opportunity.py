from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import (
    BOOutcomeType,
    OpportunitySourceType,
    OpportunityStageType,
    OpportunityType,
)


class BOCreate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    opportunity_type: OpportunityType
    opportunity_stage: OpportunityStageType = OpportunityStageType.identified
    opportunity_source: Optional[OpportunitySourceType] = None
    expected_amount: float = Field(..., gt=0)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class BOUpdate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    opportunity_type: Optional[OpportunityType] = None
    opportunity_stage: Optional[OpportunityStageType] = None
    opportunity_source: Optional[OpportunitySourceType] = None
    expected_amount: Optional[float] = Field(None, gt=0)
    due_date: Optional[date] = None
    notes: Optional[str] = None
    outcome: Optional[BOOutcomeType] = None
    outcome_date: Optional[date] = None
    outcome_amount: Optional[float] = Field(None, ge=0)


class BOResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    client_name: Optional[str] = None
    lead_name: Optional[str] = None
    opportunity_type: OpportunityType
    opportunity_stage: OpportunityStageType
    opportunity_source: Optional[OpportunitySourceType] = None
    expected_amount: Optional[float] = None
    due_date: Optional[date] = None
    due_time: Optional[str] = None
    notes: Optional[str] = None
    outcome: Optional[BOOutcomeType] = None
    outcome_date: Optional[date] = None
    outcome_amount: Optional[float] = None
    tat_days: Optional[int] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BOListResponse(BaseModel):
    opportunities: List[BOResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class BOPipelineStage(BaseModel):
    stage: str
    count: int
    total_amount: float
    opportunities: List[BOResponse]


class BOPipelineResponse(BaseModel):
    stages: List[BOPipelineStage]
    total_open: int
    total_open_amount: float
    total_won: int
    total_won_amount: float
    total_lost: int


class BOOutcomeUpdate(BaseModel):
    outcome: BOOutcomeType
    outcome_date: date
    outcome_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
