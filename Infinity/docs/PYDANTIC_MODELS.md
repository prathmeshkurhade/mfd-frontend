# MFD Digital Diary - Pydantic Models

All request/response schemas for the FastAPI backend.

---

## Table of Contents

1. [Common](#1-common)
2. [Enums](#2-enums)
3. [Profile](#3-profile)
4. [Client](#4-client)
5. [Lead](#5-lead)
6. [Task](#6-task)
7. [Touchpoint](#7-touchpoint)
8. [Business Opportunity](#8-business-opportunity)
9. [Goal](#9-goal)
10. [Calculator](#10-calculator)
11. [Document](#11-document)
12. [Campaign](#12-campaign)
13. [Notification](#13-notification)
14. [Communication](#14-communication)

---

## 1. Common

**File:** `app/models/common.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime
from uuid import UUID

T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response"""
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int


class SuccessMessage(BaseModel):
    """Simple success response"""
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    code: Optional[str] = None


class DeleteResponse(BaseModel):
    """Delete operation response"""
    message: str = "Deleted successfully"
    id: UUID


class BulkDeleteResponse(BaseModel):
    """Bulk delete response"""
    message: str
    deleted_count: int
    failed_count: int = 0
    failed_ids: List[UUID] = []
```

---

## 2. Enums

**File:** `app/constants/enums.py`

```python
from enum import Enum


class GenderType(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class MaritalStatusType(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widower = "widower"
    separated = "separated"
    dont_know = "dont_know"


class OccupationType(str, Enum):
    service = "service"
    business = "business"
    retired = "retired"
    professional = "professional"
    student = "student"
    self_employed = "self_employed"
    housemaker = "housemaker"
    dont_know = "dont_know"


class IncomeGroupType(str, Enum):
    zero = "zero"
    one_to_2_5 = "1_to_2_5"
    two_6_to_8_8 = "2_6_to_8_8"
    eight_9_to_12 = "8_9_to_12"
    twelve_1_to_24 = "12_1_to_24"
    twenty_four_1_to_48 = "24_1_to_48"
    forty_eight_1_plus = "48_1_plus"
    dont_know = "dont_know"


class AgeGroupType(str, Enum):
    below_18 = "below_18"
    eighteen_to_24 = "18_to_24"
    twenty_five_to_35 = "25_to_35"
    thirty_six_to_45 = "36_to_45"
    forty_six_to_55 = "46_to_55"
    fifty_six_plus = "56_plus"
    dont_know = "dont_know"


class RiskProfileType(str, Enum):
    conservative = "conservative"
    moderately_conservative = "moderately_conservative"
    moderate = "moderate"
    moderately_aggressive = "moderately_aggressive"
    aggressive = "aggressive"


class SourceType(str, Enum):
    natural_market = "natural_market"
    referral = "referral"
    social_networking = "social_networking"
    business_group = "business_group"
    marketing_activity = "marketing_activity"
    iap = "iap"
    cold_call = "cold_call"
    social_media = "social_media"


class LeadStatusType(str, Enum):
    follow_up = "follow_up"
    meeting_scheduled = "meeting_scheduled"
    cancelled = "cancelled"
    converted = "converted"


class TaskPriorityType(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TaskStatusType(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"
    carried_forward = "carried_forward"


class TaskMediumType(str, Enum):
    call = "call"
    whatsapp = "whatsapp"
    email = "email"
    in_person = "in_person"
    video_call = "video_call"


class InteractionType(str, Enum):
    meeting_office = "meeting_office"
    meeting_home = "meeting_home"
    cafe = "cafe"
    restaurant = "restaurant"
    call = "call"
    video_call = "video_call"


class TouchpointStatusType(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class OpportunityStageType(str, Enum):
    identified = "identified"
    inbound = "inbound"
    proposed = "proposed"


class OpportunityType(str, Enum):
    sip = "sip"
    lumpsum = "lumpsum"
    swp = "swp"
    ncd = "ncd"
    fd = "fd"
    life_insurance = "life_insurance"
    health_insurance = "health_insurance"
    las = "las"


class OpportunitySourceType(str, Enum):
    goal_planning = "goal_planning"
    portfolio_rebalancing = "portfolio_rebalancing"
    client_servicing = "client_servicing"
    financial_activities = "financial_activities"


class BOOutcomeType(str, Enum):
    open = "open"
    won = "won"
    lost = "lost"


class GoalType(str, Enum):
    retirement = "retirement"
    child_education = "child_education"
    cash_surplus = "cash_surplus"
    lifestyle = "lifestyle"
    car_purchase = "car_purchase"
    bike_purchase = "bike_purchase"
    vacation = "vacation"
    wedding = "wedding"
    home_renovation = "home_renovation"
    emergency_fund = "emergency_fund"
    wealth_creation = "wealth_creation"
    other = "other"


class GoalStatusType(str, Enum):
    active = "active"
    on_track = "on_track"
    behind = "behind"
    achieved = "achieved"
    paused = "paused"


class LifestyleSubtype(str, Enum):
    vacation_domestic = "vacation_domestic"
    vacation_international = "vacation_international"
    wedding = "wedding"
    home_renovation = "home_renovation"
    jewellery = "jewellery"
    gadgets = "gadgets"
    emergency_fund = "emergency_fund"
    car = "car"
    bike = "bike"
    other = "other"


class VehicleType(str, Enum):
    car = "car"
    bike = "bike"


class AUMBracketType(str, Enum):
    less_than_10_lakhs = "less_than_10_lakhs"
    ten_to_25_lakhs = "10_to_25_lakhs"
    twenty_five_to_50_lakhs = "25_to_50_lakhs"
    fifty_lakhs_to_1_cr = "50_lakhs_to_1_cr"
    one_cr_plus = "1_cr_plus"


class SIPBracketType(str, Enum):
    zero = "zero"
    upto_5k = "upto_5k"
    five_1k_to_10k = "5_1k_to_10k"
    ten_1k_to_25k = "10_1k_to_25k"
    twenty_five_1k_to_50k = "25_1k_to_50k"
    fifty_1k_to_1_lakh = "50_1k_to_1_lakh"
    one_lakh_plus = "1_lakh_plus"
```

---

## 3. Profile

**File:** `app/models/profile.py`

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, time
from uuid import UUID

from app.constants.enums import GenderType


# ==================== CREATE ====================
class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[GenderType] = None
    area: Optional[str] = Field(None, max_length=255)


# ==================== UPDATE ====================
class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+91[0-9]{10}$")
    age: Optional[int] = Field(None, ge=18, le=100)
    gender: Optional[GenderType] = None
    area: Optional[str] = Field(None, max_length=255)
    num_employees: Optional[int] = Field(None, ge=0)
    employee_names: Optional[str] = None
    eod_time: Optional[time] = None
    notification_email: Optional[bool] = None
    notification_whatsapp: Optional[bool] = None
    notification_push: Optional[bool] = None


# ==================== RESPONSE ====================
class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    age: Optional[int] = None
    gender: Optional[GenderType] = None
    area: Optional[str] = None
    num_employees: int = 0
    employee_names: Optional[str] = None
    eod_time: Optional[time] = None
    
    # Google
    google_connected: bool = False
    google_email: Optional[str] = None
    
    # Notifications
    notification_email: bool = True
    notification_whatsapp: bool = True
    notification_push: bool = True
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== GOOGLE OAUTH ====================
class GoogleConnectResponse(BaseModel):
    auth_url: str
    message: str = "Redirect user to auth_url"


class GoogleCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class GoogleStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    drive_folder_id: Optional[str] = None
    sheet_id: Optional[str] = None
```

---

## 4. Client

**File:** `app/models/client.py`

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import (
    GenderType, MaritalStatusType, OccupationType, 
    IncomeGroupType, RiskProfileType, SourceType,
    AgeGroupType, AUMBracketType, SIPBracketType
)


# ==================== CREATE ====================
class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    birthdate: Optional[date] = None
    
    # Demographics
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    
    # Address
    address: Optional[str] = None
    area: Optional[str] = None
    
    # Source
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    
    # Insurance
    term_insurance: bool = False
    term_insurance_amount: Optional[float] = None
    health_insurance: bool = False
    health_insurance_amount: Optional[float] = None
    
    # Risk
    risk_profile: Optional[RiskProfileType] = None
    
    # Notes
    notes: Optional[str] = None


# ==================== UPDATE ====================
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
    area: Optional[str] = None
    term_insurance: Optional[bool] = None
    term_insurance_amount: Optional[float] = None
    health_insurance: Optional[bool] = None
    health_insurance_amount: Optional[float] = None
    risk_profile: Optional[RiskProfileType] = None
    aum: Optional[float] = Field(None, ge=0)
    sip_amount: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


# ==================== RESPONSE ====================
class ClientResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    birthdate: Optional[date] = None
    
    # Calculated
    age: Optional[int] = None
    age_group: Optional[AgeGroupType] = None
    
    # Demographics
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    
    # Address
    address: Optional[str] = None
    area: Optional[str] = None
    
    # Source
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    
    # Insurance
    term_insurance: bool = False
    term_insurance_amount: Optional[float] = None
    health_insurance: bool = False
    health_insurance_amount: Optional[float] = None
    
    # Risk & Portfolio
    risk_profile: Optional[RiskProfileType] = None
    aum: Optional[float] = None
    aum_bracket: Optional[AUMBracketType] = None
    sip_amount: Optional[float] = None
    sip_bracket: Optional[SIPBracketType] = None
    
    # Conversion
    converted_from_lead_id: Optional[UUID] = None
    lead_tat_days: Optional[int] = None
    
    # Notes
    notes: Optional[str] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class ClientListResponse(BaseModel):
    clients: List[ClientResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== OVERVIEW ====================
class ClientOverview(BaseModel):
    client: ClientResponse
    goals: List[Dict[str, Any]] = []
    recent_touchpoints: List[Dict[str, Any]] = []
    open_opportunities: List[Dict[str, Any]] = []
    pending_tasks: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}


# ==================== CASH FLOW ====================
class CashFlowItem(BaseModel):
    amount: float = 0
    frequency: str = "monthly"  # monthly or yearly


class LoanItem(BaseModel):
    emi: float = 0
    pending: float = 0


class ClientCashFlowUpdate(BaseModel):
    insurance_premiums: Optional[Dict[str, float]] = None  # {life: 5000, health: 10000, ...}
    savings: Optional[Dict[str, CashFlowItem]] = None
    loans: Optional[Dict[str, LoanItem]] = None
    expenses: Optional[Dict[str, float]] = None
    income: Optional[Dict[str, float]] = None
    current_investments: Optional[Dict[str, float]] = None


class ClientCashFlowResponse(BaseModel):
    id: UUID
    client_id: UUID
    insurance_premiums: Dict[str, Any] = {}
    savings: Dict[str, Any] = {}
    loans: Dict[str, Any] = {}
    expenses: Dict[str, Any] = {}
    income: Dict[str, Any] = {}
    current_investments: Dict[str, Any] = {}
    
    # Calculated
    total_income_yearly: float = 0
    total_expenses_yearly: float = 0
    total_pending_loans: float = 0
    cash_surplus_yearly: float = 0
    cash_surplus_monthly: float = 0
    
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== DUPLICATE CHECK ====================
class DuplicateCheckRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_client: Optional[Dict[str, Any]] = None


# ==================== CONVERT FROM LEAD ====================
class ConvertLeadRequest(BaseModel):
    lead_id: UUID
    birthdate: date
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    risk_profile: Optional[RiskProfileType] = None
```

---

## 5. Lead

**File:** `app/models/lead.py`

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import (
    GenderType, MaritalStatusType, OccupationType,
    IncomeGroupType, SourceType, LeadStatusType
)


# ==================== CREATE ====================
class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    
    # Demographics
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    
    # Source
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    
    # Status
    status: LeadStatusType = LeadStatusType.follow_up
    scheduled_date: Optional[date] = None
    
    # Notes
    notes: Optional[str] = None


# ==================== UPDATE ====================
class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, pattern=r"^\+91[0-9]{10}$")
    email: Optional[EmailStr] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    status: Optional[LeadStatusType] = None
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None


# ==================== RESPONSE ====================
class LeadResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    gender: Optional[GenderType] = None
    marital_status: Optional[MaritalStatusType] = None
    occupation: Optional[OccupationType] = None
    income_group: Optional[IncomeGroupType] = None
    source: Optional[SourceType] = None
    referred_by: Optional[str] = None
    status: LeadStatusType
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== STATUS UPDATE ====================
class LeadStatusUpdate(BaseModel):
    status: LeadStatusType
    scheduled_date: Optional[date] = None
    notes: Optional[str] = None
```

---

## 6. Task

**File:** `app/models/task.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import (
    TaskPriorityType, TaskStatusType, TaskMediumType
)


# ==================== CREATE ====================
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    
    # Links
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    touchpoint_id: Optional[UUID] = None
    bo_id: Optional[UUID] = None
    
    # Details
    priority: TaskPriorityType = TaskPriorityType.medium
    medium: Optional[TaskMediumType] = None
    due_date: date
    
    # Reminders
    reminder_date: Optional[date] = None
    reminder_time: Optional[str] = None  # HH:MM format


# ==================== UPDATE ====================
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriorityType] = None
    medium: Optional[TaskMediumType] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatusType] = None
    reminder_date: Optional[date] = None
    reminder_time: Optional[str] = None


# ==================== RESPONSE ====================
class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str] = None
    
    # Links
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    touchpoint_id: Optional[UUID] = None
    bo_id: Optional[UUID] = None
    
    # Details
    priority: TaskPriorityType
    medium: Optional[TaskMediumType] = None
    due_date: date
    status: TaskStatusType
    
    # Carry forward
    original_date: Optional[date] = None
    carry_forward_count: int = 0
    
    # Completion
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    
    # Reminders
    reminder_date: Optional[date] = None
    reminder_time: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== COMPLETE ====================
class TaskCompleteRequest(BaseModel):
    completion_notes: Optional[str] = None


# ==================== CARRY FORWARD ====================
class TaskCarryForwardRequest(BaseModel):
    new_date: date
    reason: Optional[str] = None


# ==================== BULK ====================
class BulkTaskCreate(BaseModel):
    tasks: List[TaskCreate]


class BulkTaskStatusUpdate(BaseModel):
    task_ids: List[UUID]
    status: TaskStatusType
```

---

## 7. Touchpoint

**File:** `app/models/touchpoint.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import InteractionType, TouchpointStatusType


# ==================== CREATE ====================
class TouchpointCreate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    
    interaction_type: InteractionType
    scheduled_date: date
    scheduled_time: Optional[str] = None  # HH:MM
    
    location: Optional[str] = None
    agenda: Optional[str] = None


# ==================== UPDATE ====================
class TouchpointUpdate(BaseModel):
    interaction_type: Optional[InteractionType] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[TouchpointStatusType] = None


# ==================== RESPONSE ====================
class TouchpointResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    
    interaction_type: InteractionType
    scheduled_date: date
    scheduled_time: Optional[str] = None
    
    location: Optional[str] = None
    agenda: Optional[str] = None
    status: TouchpointStatusType
    
    # MoM
    mom_raw: Optional[str] = None
    mom_structured: Optional[Dict[str, Any]] = None
    mom_pdf_url: Optional[str] = None
    
    # Completion
    actual_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class TouchpointListResponse(BaseModel):
    touchpoints: List[TouchpointResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== COMPLETE ====================
class TouchpointCompleteRequest(BaseModel):
    actual_date: Optional[date] = None
    duration_minutes: Optional[int] = None
    mom_raw: Optional[str] = None


# ==================== MOM ====================
class MoMUpdateRequest(BaseModel):
    mom_raw: str


class MoMStructuredResponse(BaseModel):
    """AI-structured MoM [COLLABORATIVE]"""
    key_points: List[str] = []
    action_items: List[Dict[str, Any]] = []
    decisions: List[str] = []
    next_steps: List[str] = []
    followup_date: Optional[date] = None


# ==================== RESCHEDULE ====================
class RescheduleRequest(BaseModel):
    new_date: date
    new_time: Optional[str] = None
    reason: Optional[str] = None
```

---

## 8. Business Opportunity

**File:** `app/models/business_opportunity.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import (
    OpportunityStageType, OpportunityType, 
    OpportunitySourceType, BOOutcomeType
)


# ==================== CREATE ====================
class BOCreate(BaseModel):
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    
    opportunity_type: OpportunityType
    opportunity_stage: OpportunityStageType = OpportunityStageType.identified
    opportunity_source: Optional[OpportunitySourceType] = None
    
    product_name: Optional[str] = None
    expected_amount: Optional[float] = Field(None, ge=0)
    
    due_date: Optional[date] = None
    notes: Optional[str] = None


# ==================== UPDATE ====================
class BOUpdate(BaseModel):
    opportunity_type: Optional[OpportunityType] = None
    opportunity_stage: Optional[OpportunityStageType] = None
    opportunity_source: Optional[OpportunitySourceType] = None
    product_name: Optional[str] = None
    expected_amount: Optional[float] = Field(None, ge=0)
    due_date: Optional[date] = None
    notes: Optional[str] = None


# ==================== RESPONSE ====================
class BOResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    
    opportunity_type: OpportunityType
    opportunity_stage: OpportunityStageType
    opportunity_source: Optional[OpportunitySourceType] = None
    
    product_name: Optional[str] = None
    expected_amount: Optional[float] = None
    
    due_date: Optional[date] = None
    notes: Optional[str] = None
    
    # Outcome
    outcome: BOOutcomeType = BOOutcomeType.open
    outcome_date: Optional[date] = None
    outcome_amount: Optional[float] = None
    outcome_notes: Optional[str] = None
    
    # TAT
    tat_days: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class BOListResponse(BaseModel):
    opportunities: List[BOResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== OUTCOME ====================
class BOOutcomeRequest(BaseModel):
    outcome: BOOutcomeType
    outcome_amount: Optional[float] = Field(None, ge=0)
    outcome_notes: Optional[str] = None


# ==================== PIPELINE ====================
class BOPipelineResponse(BaseModel):
    identified: List[BOResponse] = []
    inbound: List[BOResponse] = []
    proposed: List[BOResponse] = []
    
    total_expected: float = 0
    total_count: int = 0


# ==================== STAGE UPDATE ====================
class BOStageUpdate(BaseModel):
    opportunity_stage: OpportunityStageType
    notes: Optional[str] = None
```

---

## 9. Goal

**File:** `app/models/goal.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID

from app.constants.enums import (
    GoalType, GoalStatusType, LifestyleSubtype, VehicleType
)


# ==================== PRODUCT ALLOCATION ====================
class ProductAllocation(BaseModel):
    product_code: str
    product_name: str
    allocation_percent: Optional[float] = None
    amount: Optional[float] = None
    investment_type: str = "sip"  # sip or lumpsum


# ==================== CREATE ====================
class GoalCreate(BaseModel):
    client_id: UUID
    
    goal_type: GoalType
    goal_name: str = Field(..., min_length=1, max_length=255)
    
    # For education sub-goals
    parent_goal_id: Optional[UUID] = None
    child_name: Optional[str] = None
    child_current_age: Optional[int] = Field(None, ge=0, le=30)
    
    # For lifestyle
    lifestyle_subtype: Optional[LifestyleSubtype] = None
    
    # For car/bike
    vehicle_type: Optional[VehicleType] = None
    
    # Target
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    
    # Investment plan
    current_investment: float = Field(0, ge=0)
    monthly_sip: float = Field(0, ge=0)
    lumpsum_investment: float = Field(0, ge=0)
    expected_return_rate: Optional[float] = Field(None, ge=0, le=30)
    
    # Products
    products: Optional[List[ProductAllocation]] = None


# ==================== UPDATE ====================
class GoalUpdate(BaseModel):
    goal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    current_investment: Optional[float] = Field(None, ge=0)
    monthly_sip: Optional[float] = Field(None, ge=0)
    lumpsum_investment: Optional[float] = Field(None, ge=0)
    expected_return_rate: Optional[float] = Field(None, ge=0, le=30)
    status: Optional[GoalStatusType] = None
    products: Optional[List[ProductAllocation]] = None


# ==================== RESPONSE ====================
class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: UUID
    
    goal_type: GoalType
    goal_name: str
    
    # Sub-goal fields
    parent_goal_id: Optional[UUID] = None
    child_name: Optional[str] = None
    child_current_age: Optional[int] = None
    
    lifestyle_subtype: Optional[LifestyleSubtype] = None
    vehicle_type: Optional[VehicleType] = None
    
    # Target
    target_amount: float
    target_date: Optional[date] = None
    target_age: Optional[int] = None
    
    # Investment
    current_investment: float = 0
    monthly_sip: float = 0
    lumpsum_investment: float = 0
    expected_return_rate: Optional[float] = None
    
    # Products
    products: Optional[List[Dict[str, Any]]] = None
    
    # Calculator data
    calculator_type: Optional[str] = None
    calculator_inputs: Optional[Dict[str, Any]] = None
    calculator_outputs: Optional[Dict[str, Any]] = None
    
    # Progress
    progress_percent: float = 0
    status: GoalStatusType
    
    # PDF
    pdf_url: Optional[str] = None
    pdf_generated_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class GoalListResponse(BaseModel):
    goals: List[GoalResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# ==================== WITH SUB-GOALS ====================
class GoalWithSubgoals(BaseModel):
    """For education goals with multiple milestones"""
    parent: GoalResponse
    sub_goals: List[GoalResponse] = []
    total_target: float = 0
    total_monthly_sip: float = 0
```

---

## 10. Calculator

**File:** `app/models/calculator.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.constants.enums import LifestyleSubtype, VehicleType


# ==================== INVESTMENT PRODUCTS ====================
class InvestmentProductResponse(BaseModel):
    id: UUID
    name: str
    code: str
    default_return_rate: float
    supports_sip: bool
    supports_lumpsum: bool


# ==================== SIP CALCULATOR ====================
class SIPCalculatorRequest(BaseModel):
    monthly_sip: float = Field(..., gt=0)
    tenure_years: int = Field(..., ge=1, le=50)
    expected_return: float = Field(..., ge=0, le=30)
    step_up_type: str = "none"  # none, amount, percent
    step_up_value: float = Field(0, ge=0)


class TaxCalculation(BaseModel):
    stcg: float = 0
    ltcg: float = 0
    total_tax: float = 0


class SIPCalculatorResponse(BaseModel):
    total_investment: float
    total_gains: float
    final_value: float
    returns_percent: float
    tax_calculation: TaxCalculation
    net_returns_after_tax: float


# ==================== LUMPSUM CALCULATOR ====================
class LumpsumCalculatorRequest(BaseModel):
    lumpsum_amount: float = Field(..., gt=0)
    tenure_years: int = Field(..., ge=1, le=50)
    expected_return: float = Field(..., ge=0, le=30)


class LumpsumCalculatorResponse(BaseModel):
    lumpsum_amount: float
    final_value: float
    total_gains: float
    returns_percent: float
    tax_calculation: TaxCalculation
    net_returns_after_tax: float


# ==================== RETIREMENT CALCULATOR ====================
class RetirementCalculatorRequest(BaseModel):
    client_id: Optional[UUID] = None
    current_age: int = Field(..., ge=18, le=80)
    retirement_age: int = Field(..., ge=30, le=80)
    life_expectancy: int = Field(..., ge=50, le=100)
    current_monthly_expense: float = Field(..., gt=0)
    pre_retirement_inflation: float = Field(6, ge=0, le=20)
    post_retirement_inflation: float = Field(6, ge=0, le=20)
    expected_return: float = Field(12, ge=0, le=30)
    post_retirement_return: float = Field(7, ge=0, le=20)
    current_investments: Dict[str, float] = {}  # {product_code: amount}
    irregular_cash_flows: List[Dict[str, Any]] = []  # [{year: 5, amount: 100000}]
    expected_lumpsums: List[Dict[str, Any]] = []  # [{year: 10, amount: 500000}]


class InvestmentOptions(BaseModel):
    monthly_sip: float
    yearly_investment: float
    one_time_lumpsum: float


class StepUpOptions(BaseModel):
    step_up_amount: Dict[str, float] = {}  # {amount: 2500, starting_sip: 35000}
    step_up_percent: Dict[str, float] = {}  # {percent: 10, starting_sip: 28000}


class RetirementCalculatorResponse(BaseModel):
    years_to_retirement: int
    retirement_duration: int
    monthly_expense_at_retirement: float
    corpus_needed: float
    current_investments_fv: float
    shortfall: float
    investment_options: InvestmentOptions
    step_up_options: Optional[StepUpOptions] = None


# ==================== EDUCATION CALCULATOR ====================
class EducationGoalInput(BaseModel):
    name: str  # e.g., "8th-10th STD"
    target_age: int = Field(..., ge=1, le=30)
    current_cost: float = Field(..., gt=0)


class ChildInput(BaseModel):
    name: str
    current_age: int = Field(..., ge=0, le=25)
    goals: List[EducationGoalInput]


class EducationCalculatorRequest(BaseModel):
    client_id: Optional[UUID] = None
    children: List[ChildInput]
    investment_product: str = "mutual_funds"
    expected_return: float = Field(12, ge=0, le=30)
    education_inflation: float = Field(10, ge=0, le=20)


class EducationGoalOutput(BaseModel):
    name: str
    target_age: int
    years_to_goal: int
    current_cost: float
    future_value: float
    monthly_sip: float
    yearly_investment: float
    one_time_lumpsum: float


class ChildOutput(BaseModel):
    name: str
    current_age: int
    goals: List[EducationGoalOutput]
    total_future_value: float
    total_monthly_sip: float


class EducationSummary(BaseModel):
    total_children: int
    total_goals: int
    total_future_corpus: float
    total_monthly_sip: float
    total_yearly: float
    total_one_time: float


class EducationCalculatorResponse(BaseModel):
    children: List[ChildOutput]
    summary: EducationSummary


# ==================== CASH SURPLUS CALCULATOR ====================
class CashSurplusCalculatorRequest(BaseModel):
    client_id: UUID
    insurance_premiums: Dict[str, float] = {}  # {life: 5000, health: 10000, motor: 3000}
    savings: Dict[str, Dict[str, Any]] = {}  # {mutual_funds: {amount: 10000, frequency: "monthly"}}
    loans: Dict[str, Dict[str, float]] = {}  # {home_loan: {emi: 25000, pending: 2500000}}
    expenses: Dict[str, float] = {}  # {rent: 15000, grocery: 8000}
    income: Dict[str, float] = {}  # {salary: 150000, rent_income: 0}
    current_investments: Dict[str, float] = {}  # {mutual_funds: 500000}


class ExpenseBreakdown(BaseModel):
    insurance: float
    savings: float
    loan_emi: float
    lifestyle: float


class CashSurplusCalculatorResponse(BaseModel):
    total_income_yearly: float
    total_expenses_yearly: float
    expense_breakdown: ExpenseBreakdown
    total_pending_loans: float
    cash_surplus_yearly: float
    cash_surplus_monthly: float
    total_portfolio: float


# ==================== INSURANCE CALCULATOR (HLV) ====================
class InsuranceCalculatorRequest(BaseModel):
    client_id: Optional[UUID] = None
    annual_income: float = Field(..., gt=0)
    current_age: int = Field(..., ge=18, le=80)
    retirement_age: int = Field(..., ge=30, le=80)
    existing_life_cover: float = Field(0, ge=0)
    existing_liabilities: float = Field(0, ge=0)
    annual_expenses: float = Field(0, ge=0)
    dependants: int = Field(0, ge=0)


class InsuranceCalculatorResponse(BaseModel):
    hlv_calculated: float
    existing_cover: float
    cover_gap: float
    recommended_term_cover: float
    health_cover_recommended: float


# ==================== CAR/BIKE CALCULATOR ====================
class CarBikeCalculatorRequest(BaseModel):
    client_id: Optional[UUID] = None
    vehicle_type: VehicleType
    target_amount: float = Field(..., gt=0)
    target_years: int = Field(..., ge=1, le=10)
    down_payment_available: float = Field(0, ge=0)
    expected_return: float = Field(12, ge=0, le=30)
    include_loan_option: bool = True


class LoanOption(BaseModel):
    loan_amount: float
    tenure_years: int
    interest_rate: float
    emi: float


class CarBikeCalculatorResponse(BaseModel):
    target_amount: float
    down_payment: float
    amount_to_accumulate: float
    investment_options: InvestmentOptions
    loan_option: Optional[LoanOption] = None


# ==================== LIFESTYLE CALCULATOR ====================
class LifestyleCalculatorRequest(BaseModel):
    client_id: Optional[UUID] = None
    lifestyle_subtype: LifestyleSubtype
    goal_name: str
    target_amount: float = Field(..., gt=0)
    target_years: int = Field(..., ge=1, le=30)
    current_savings: float = Field(0, ge=0)
    expected_return: float = Field(12, ge=0, le=30)
    inflation_rate: float = Field(6, ge=0, le=20)


class LifestyleCalculatorResponse(BaseModel):
    goal_name: str
    future_value: float
    current_savings_fv: float
    gap: float
    investment_options: InvestmentOptions


# ==================== RISK APPETITE CALCULATOR ====================
class RiskAppetiteRequest(BaseModel):
    client_id: Optional[UUID] = None
    answers: Dict[str, str]  # {q1: "a", q2: "c", ...}


class RecommendedAllocation(BaseModel):
    equity: int
    debt: int
    gold: int


class RiskAppetiteResponse(BaseModel):
    score: int
    risk_profile: str
    recommended_allocation: RecommendedAllocation


# ==================== SAVE AS GOAL ====================
class SaveAsGoalRequest(BaseModel):
    calculator_type: str
    client_id: UUID
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    goal_name: str
    products: List[Dict[str, Any]] = []


class SaveAsGoalResponse(BaseModel):
    calculator_result_id: UUID
    goal_id: UUID
    pdf_url: Optional[str] = None
    message: str


# ==================== CALCULATOR HISTORY ====================
class CalculatorHistoryItem(BaseModel):
    id: UUID
    calculator_type: str
    client_id: Optional[UUID]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    linked_goal_id: Optional[UUID] = None
    created_at: datetime


class CalculatorHistoryResponse(BaseModel):
    results: List[CalculatorHistoryItem]
    total: int
```

---

## 11. Document

**File:** `app/models/document.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ==================== UPLOAD ====================
class DocumentUploadRequest(BaseModel):
    client_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    document_type: Optional[str] = None  # goal_pdf, mom_pdf, pan, aadhar, etc.
    related_entity_type: Optional[str] = None  # goal, touchpoint, calculator
    related_entity_id: Optional[UUID] = None


# ==================== RESPONSE ====================
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

    class Config:
        from_attributes = True


# ==================== LIST ====================
class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


# ==================== SHARE ====================
class ShareDocumentRequest(BaseModel):
    via: str = "whatsapp"  # whatsapp or email
    message: Optional[str] = None
```

---

## 12. Campaign

**File:** `app/models/campaign.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from uuid import UUID


# ==================== CREATE ====================
class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    campaign_type: str  # birthday, insurance_renewal, sip_reminder, custom
    
    # Filters for clients
    filters: Dict[str, Any] = {}  # {age_group: "25_to_35", area: "Mumbai"}
    
    # Message
    message_template: str
    channel: str = "whatsapp"  # whatsapp or email
    
    # Schedule
    scheduled_date: Optional[date] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly


# ==================== UPDATE ====================
class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    message_template: Optional[str] = None
    channel: Optional[str] = None
    scheduled_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== RESPONSE ====================
class CampaignResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    description: Optional[str] = None
    campaign_type: str
    filters: Dict[str, Any] = {}
    message_template: str
    channel: str
    scheduled_date: Optional[date] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    is_active: bool = True
    
    # Stats
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    last_run_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class CampaignListResponse(BaseModel):
    campaigns: List[CampaignResponse]
    total: int


# ==================== PREVIEW ====================
class CampaignPreviewResponse(BaseModel):
    campaign_id: UUID
    total_recipients: int
    sample_recipients: List[Dict[str, Any]] = []
    sample_message: str


# ==================== EXECUTE ====================
class CampaignExecuteResponse(BaseModel):
    campaign_id: UUID
    total_sent: int
    total_failed: int
    message: str
```

---

## 13. Notification

**File:** `app/models/notification.py`

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ==================== RESPONSE ====================
class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    notification_type: str  # task_reminder, birthday, meeting, etc.
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[UUID] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== LIST ====================
class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


# ==================== MARK READ ====================
class MarkReadRequest(BaseModel):
    notification_ids: List[UUID]


class MarkReadResponse(BaseModel):
    marked_count: int
    message: str
```

---

## 14. Communication

**File:** `app/models/communication.py`

```python
"""
Communication Models
[TEAM] - WhatsApp & Email implementation by other intern
These schemas define the interface only
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ==================== WHATSAPP [TEAM] ====================
class WhatsAppMessageRequest(BaseModel):
    client_id: UUID
    message: str
    template_id: Optional[str] = None
    template_params: Optional[Dict[str, str]] = None


class WhatsAppDocumentRequest(BaseModel):
    client_id: UUID
    document_id: UUID
    caption: Optional[str] = None


class WhatsAppMessageResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str  # sent, pending, failed
    error: Optional[str] = None


class WhatsAppTemplate(BaseModel):
    id: str
    name: str
    content: str
    params: List[str] = []


class WhatsAppTemplateListResponse(BaseModel):
    templates: List[WhatsAppTemplate]


# ==================== EMAIL [TEAM] ====================
class EmailRequest(BaseModel):
    client_id: UUID
    to_email: EmailStr
    subject: str
    body: str
    is_html: bool = False
    attachments: List[UUID] = []  # document IDs


class EmailResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    status: str
    error: Optional[str] = None


# ==================== COMMUNICATION LOG ====================
class CommunicationLogResponse(BaseModel):
    id: UUID
    user_id: UUID
    client_id: UUID
    channel: str  # whatsapp, email, sms
    message_type: str  # text, document, template
    content: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class CommunicationHistoryResponse(BaseModel):
    logs: List[CommunicationLogResponse]
    total: int
```

---

## Summary

| Module | Schemas Count |
|--------|---------------|
| Common | 5 |
| Enums | 25 |
| Profile | 6 |
| Client | 12 |
| Lead | 5 |
| Task | 8 |
| Touchpoint | 7 |
| Business Opportunity | 7 |
| Goal | 6 |
| Calculator | 25 |
| Document | 4 |
| Campaign | 6 |
| Notification | 4 |
| Communication | 9 |
| **Total** | **~129 schemas** |

---

## How to Use

1. **Copy each section** to its corresponding file in `app/models/`
2. **Import enums** from `app/constants/enums.py` where needed
3. **Cursor can generate** routers and services using these schemas + API_ENDPOINTS.md

---
