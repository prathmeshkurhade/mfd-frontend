"""Pydantic models for WhatsApp form endpoints.

Each form requires mfd_phone (10-digit number) to identify the MFD,
plus form-specific required fields that match the underlying service models.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import (
    AgeGroupType,
    BOOutcomeType,
    GenderType,
    IncomeGroupType,
    InteractionType,
    LeadStatusType,
    MaritalStatusType,
    OccupationType,
    OpportunitySourceType,
    OpportunityStageType,
    OpportunityType,
    SourceType,
    TaskMediumType,
    TaskPriorityType,
    TouchpointStatusType,
)


# ──────────────────────────────────────────────
# Base — every WhatsApp form must identify the MFD
# ──────────────────────────────────────────────

class WhatsAppFormBase(BaseModel):
    mfd_phone: str = Field(
        ...,
        pattern=r"^[0-9]{10}$",
        description="MFD's 10-digit mobile number (without +91)",
    )


# ──────────────────────────────────────────────
# Create Lead
# ──────────────────────────────────────────────

class WALeadCreate(WhatsAppFormBase):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(
        ...,
        pattern=r"^[0-9]{10}$",
        description="Lead's 10-digit phone number (without +91)",
    )
    source: SourceType
    email: Optional[str] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    age_group: Optional[AgeGroupType] = None
    area: Optional[str] = None
    referred_by: Optional[str] = None
    dependants: Optional[int] = None
    source_description: Optional[str] = None
    status: Optional[LeadStatusType] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    all_day: Optional[bool] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────────
# Create Task
# ──────────────────────────────────────────────

class WATaskCreate(WhatsAppFormBase):
    title: str = Field(..., min_length=1, max_length=255)
    due_date: date
    description: Optional[str] = None
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    priority: Optional[TaskPriorityType] = None
    medium: Optional[TaskMediumType] = None
    due_time: Optional[str] = None
    all_day: Optional[bool] = None
    product_type: Optional[str] = None
    is_business_opportunity: Optional[bool] = None


# ──────────────────────────────────────────────
# Create Touchpoint (Meeting)
# ──────────────────────────────────────────────

class WATouchpointCreate(WhatsAppFormBase):
    interaction_type: InteractionType
    scheduled_date: date
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[TouchpointStatusType] = None


# ──────────────────────────────────────────────
# Create Business Opportunity
# ──────────────────────────────────────────────

class WABOCreate(WhatsAppFormBase):
    opportunity_type: OpportunityType
    expected_amount: float = Field(..., gt=0)
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    opportunity_stage: Optional[OpportunityStageType] = None
    opportunity_source: Optional[OpportunitySourceType] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


# ──────────────────────────────────────────────
# Search (for client/lead lookup)
# ──────────────────────────────────────────────

class WASearchRequest(WhatsAppFormBase):
    query: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(
        ...,
        pattern=r"^(client|lead)$",
        description="Search for 'client' or 'lead'",
    )


class WASearchResult(BaseModel):
    id: str
    name: str


class WASearchResponse(BaseModel):
    results: List[WASearchResult]
    total: int


# ──────────────────────────────────────────────
# Common response
# ──────────────────────────────────────────────

class WAFormResponse(BaseModel):
    status: str
    message: str
    entity_id: Optional[str] = None
    errors: Optional[dict] = None
