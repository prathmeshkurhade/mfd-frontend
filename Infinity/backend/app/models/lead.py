from datetime import date, datetime
from typing import Annotated, List, Optional
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, EmailStr, Field

from app.constants.enums import (
    AgeGroupType,
    GenderType,
    IncomeGroupType,
    LeadStatusType,
    MaritalStatusType,
    OccupationType,
    SourceType,
)


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    age_group: Optional[AgeGroupType] = None
    area: Optional[str] = None
    source: SourceType
    referred_by: Optional[str] = None
    dependants: Optional[int] = None
    source_description: Optional[str] = None
    status: LeadStatusType = LeadStatusType.follow_up
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    all_day: Optional[bool] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    age_group: Optional[AgeGroupType] = None
    area: Optional[str] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    dependants: Optional[int] = None
    source_description: Optional[str] = None
    status: Optional[LeadStatusType] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    all_day: Optional[bool] = None
    notes: Optional[str] = None


def _coerce_date(v: object) -> object:
    """Coerce datetime / timestamp-string to plain date for Pydantic v2.12+."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str) and "T" in v:
        return v.split("T")[0]
    return v


CoercedDate = Annotated[date, BeforeValidator(_coerce_date)]


class LeadResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    age_group: Optional[AgeGroupType] = None
    area: Optional[str] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = Field(None, validation_alias="sourced_by")
    dependants: Optional[int] = None
    source_description: Optional[str] = None
    status: LeadStatusType
    scheduled_date: Optional[CoercedDate] = None
    scheduled_time: Optional[str] = None
    all_day: Optional[bool] = None
    notes: Optional[str] = None
    converted_to_client_id: Optional[UUID] = None
    conversion_date: Optional[CoercedDate] = None
    tat_days: Optional[int] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class LeadStatusUpdate(BaseModel):
    status: LeadStatusType
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    notes: Optional[str] = None
