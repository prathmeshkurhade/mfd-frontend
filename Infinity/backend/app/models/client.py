from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.constants.enums import (
    AumBracketType,
    AgeGroupType,
    GenderType,
    IncomeGroupType,
    MaritalStatusType,
    OccupationType,
    RiskProfileType,
    SipBracketType,
    SourceType,
)


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    birthdate: Optional[date] = None
    gender: GenderType
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    address: Optional[str] = None
    area: Optional[str] = Field(None, max_length=255)
    risk_profile: Optional[RiskProfileType] = None
    source: SourceType
    referred_by: Optional[str] = None
    term_insurance: Optional[float] = None
    health_insurance: Optional[float] = None
    aum: Optional[float] = Field(None, ge=0)
    sip_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    birthdate: Optional[date] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    address: Optional[str] = None
    area: Optional[str] = Field(None, max_length=255)
    risk_profile: Optional[RiskProfileType] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    term_insurance: Optional[float] = None
    health_insurance: Optional[float] = None
    aum: Optional[float] = Field(None, ge=0)
    sip_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    email: Optional[EmailStr] = None
    birthdate: Optional[date] = None
    age: Optional[int] = None
    age_group: Optional[AgeGroupType] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    address: Optional[str] = None
    area: Optional[str] = None
    risk_profile: Optional[RiskProfileType] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = Field(None, validation_alias="sourced_by")
    term_insurance: Optional[float] = None
    health_insurance: Optional[float] = None
    aum: Optional[float] = Field(None, validation_alias="total_aum")
    aum_bracket: Optional[AumBracketType] = None
    sip_amount: Optional[float] = Field(None, validation_alias="sip")
    sip_bracket: Optional[SipBracketType] = None
    dependants: Optional[int] = None
    notes: Optional[str] = None
    converted_from_lead_id: Optional[UUID] = None
    conversion_date: Optional[date] = None
    lead_tat_days: Optional[int] = None
    google_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class ClientOverview(BaseModel):
    client: ClientResponse
    goals: List[dict]
    recent_touchpoints: List[dict]
    open_opportunities: List[dict]
    pending_tasks: List[dict]
    stats: dict


class ConvertLeadRequest(BaseModel):
    lead_id: UUID
    birthdate: date
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    risk_profile: Optional[RiskProfileType] = None


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_client: Optional[dict] = None
