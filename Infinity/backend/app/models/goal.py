from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import (
    GoalStatusType,
    GoalType,
    LifestyleSubtype,
    VehicleType,
)


class GoalProduct(BaseModel):
    name: str
    type: str  # sip or lumpsum
    amount: float
    return_rate: Optional[float] = None


class GoalCreate(BaseModel):
    client_id: UUID
    goal_type: GoalType
    goal_name: str = Field(..., min_length=1, max_length=255)
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    current_investment: float = Field(0, ge=0)
    monthly_sip: float = Field(0, ge=0)
    lumpsum_investment: float = Field(0, ge=0)
    expected_return_rate: Optional[float] = None
    products: Optional[List[GoalProduct]] = None
    parent_goal_id: Optional[UUID] = None
    child_name: Optional[str] = None
    child_current_age: Optional[int] = None
    lifestyle_subtype: Optional[LifestyleSubtype] = None
    vehicle_type: Optional[VehicleType] = None


class GoalUpdate(BaseModel):
    goal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    current_investment: Optional[float] = Field(None, ge=0)
    monthly_sip: Optional[float] = Field(None, ge=0)
    lumpsum_investment: Optional[float] = Field(None, ge=0)
    expected_return_rate: Optional[float] = None
    products: Optional[List[GoalProduct]] = None
    parent_goal_id: Optional[UUID] = None
    child_name: Optional[str] = None
    child_current_age: Optional[int] = None
    lifestyle_subtype: Optional[LifestyleSubtype] = None
    vehicle_type: Optional[VehicleType] = None
    status: Optional[GoalStatusType] = None


class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    goal_type: GoalType
    goal_name: str
    target_amount: float
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    current_investment: float = 0
    monthly_sip: float = 0
    lumpsum_investment: float = 0
    expected_return_rate: Optional[float] = None
    products: Optional[List[Dict[str, Any]]] = None
    parent_goal_id: Optional[UUID] = None
    child_name: Optional[str] = None
    child_current_age: Optional[int] = None
    lifestyle_subtype: Optional[LifestyleSubtype] = None
    vehicle_type: Optional[VehicleType] = None
    calculator_type: Optional[str] = None
    calculator_inputs: Optional[Dict[str, Any]] = None
    calculator_outputs: Optional[Dict[str, Any]] = None
    progress_percent: float = 0
    status: GoalStatusType
    pdf_url: Optional[str] = None
    pdf_generated_at: Optional[datetime] = None
    excel_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalListResponse(BaseModel):
    goals: List[GoalResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class GoalWithSubgoals(BaseModel):
    parent_goal: GoalResponse
    sub_goals: List[GoalResponse]
    total_target: float
    total_monthly_sip: float
