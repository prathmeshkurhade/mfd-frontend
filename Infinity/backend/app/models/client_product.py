from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.constants.enums import (
    ProductCategoryType,
    InvestmentTypeEnum,
    ProductStatusType,
    PremiumFrequencyType
)


class ClientProductCreate(BaseModel):
    """Schema for creating a client product"""
    client_id: UUID
    product_id: Optional[UUID] = None  # Link to master product (optional)
    product_name: str = Field(..., min_length=1, max_length=255)
    category: ProductCategoryType
    sub_category: Optional[str] = None
    provider_name: Optional[str] = None
    investment_type: InvestmentTypeEnum = InvestmentTypeEnum.lumpsum
    
    # Investment amounts
    invested_amount: float = Field(default=0, ge=0)
    current_value: float = Field(default=0, ge=0)
    units: Optional[float] = Field(None, ge=0)
    nav: Optional[float] = Field(None, ge=0)
    sip_amount: float = Field(default=0, ge=0)
    sip_date: Optional[int] = Field(None, ge=1, le=28)  # Day of month
    
    # Insurance specific
    sum_assured: Optional[float] = Field(None, ge=0)
    premium_amount: Optional[float] = Field(None, ge=0)
    premium_frequency: Optional[PremiumFrequencyType] = None
    
    # Dates
    start_date: Optional[date] = None
    maturity_date: Optional[date] = None
    next_due_date: Optional[date] = None
    
    # Identifiers
    folio_number: Optional[str] = Field(None, max_length=100)
    policy_number: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=100)
    
    # Linking
    goal_id: Optional[UUID] = None
    
    # Nominee
    nominee_name: Optional[str] = None
    nominee_relation: Optional[str] = None
    
    notes: Optional[str] = None


class ClientProductUpdate(BaseModel):
    """Schema for updating a client product - all fields optional"""
    client_id: Optional[UUID] = None
    product_id: Optional[UUID] = None
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ProductCategoryType] = None
    sub_category: Optional[str] = None
    provider_name: Optional[str] = None
    investment_type: Optional[InvestmentTypeEnum] = None
    
    # Investment amounts
    invested_amount: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    units: Optional[float] = Field(None, ge=0)
    nav: Optional[float] = Field(None, ge=0)
    sip_amount: Optional[float] = Field(None, ge=0)
    sip_date: Optional[int] = Field(None, ge=1, le=28)
    
    # Insurance specific
    sum_assured: Optional[float] = Field(None, ge=0)
    premium_amount: Optional[float] = Field(None, ge=0)
    premium_frequency: Optional[PremiumFrequencyType] = None
    
    # Dates
    start_date: Optional[date] = None
    maturity_date: Optional[date] = None
    next_due_date: Optional[date] = None
    
    # Identifiers
    folio_number: Optional[str] = Field(None, max_length=100)
    policy_number: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=100)
    
    # Linking
    goal_id: Optional[UUID] = None
    
    # Nominee
    nominee_name: Optional[str] = None
    nominee_relation: Optional[str] = None
    
    notes: Optional[str] = None
    
    # Additional update fields
    status: Optional[ProductStatusType] = None
    last_updated_date: Optional[date] = None


class ClientProductResponse(BaseModel):
    """Schema for client product response"""
    id: UUID
    user_id: UUID
    client_id: UUID
    product_id: Optional[UUID]
    product_name: str
    category: ProductCategoryType
    sub_category: Optional[str]
    provider_name: Optional[str]
    investment_type: InvestmentTypeEnum
    status: ProductStatusType
    invested_amount: float
    current_value: float
    units: Optional[float]
    nav: Optional[float]
    sip_amount: float
    sip_date: Optional[int]
    sum_assured: Optional[float]
    premium_amount: Optional[float]
    premium_frequency: Optional[PremiumFrequencyType]
    start_date: Optional[date]
    maturity_date: Optional[date]
    next_due_date: Optional[date]
    last_updated_date: Optional[date]
    folio_number: Optional[str]
    policy_number: Optional[str]
    account_number: Optional[str]
    goal_id: Optional[UUID]
    goal_name: Optional[str] = None  # Joined from goals table
    nominee_name: Optional[str]
    nominee_relation: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    gain_loss: Optional[float] = None  # current_value - invested_amount
    gain_loss_percent: Optional[float] = None  # ((current - invested) / invested) * 100
    
    class Config:
        from_attributes = True


class ClientProductListResponse(BaseModel):
    """Schema for client product list response with aggregates"""
    products: List[ClientProductResponse]
    total: int
    total_invested: float
    total_current_value: float
    total_gain_loss: float
    total_sip: float


class ClientPortfolioSummary(BaseModel):
    """Schema for client portfolio summary with comprehensive statistics"""
    client_id: UUID
    client_name: str
    total_aum: float
    total_invested: float
    total_current_value: float
    total_gain_loss: float
    total_gain_loss_percent: float
    total_sip: float
    by_category: Dict[str, float]  # {"mutual_fund": 500000, "fixed_deposit": 100000}
    by_investment_type: Dict[str, float]  # {"sip": 300000, "lumpsum": 200000}
    by_provider: Dict[str, float]  # {"HDFC AMC": 300000, "SBI AMC": 200000}
    products_count: int
    active_sips_count: int


class UpdateValueRequest(BaseModel):
    """Schema for updating product current value"""
    current_value: float = Field(..., ge=0)
    nav: Optional[float] = Field(None, ge=0)
    units: Optional[float] = Field(None, ge=0)
    last_updated_date: Optional[date] = None


class BulkUpdateValueItem(BaseModel):
    """Schema for a single item in bulk value update"""
    product_id: UUID
    current_value: float = Field(..., ge=0)
    nav: Optional[float] = None
    units: Optional[float] = None


class BulkUpdateValueRequest(BaseModel):
    """Schema for bulk updating product values"""
    updates: List[BulkUpdateValueItem]


class BulkUpdateValueResponse(BaseModel):
    """Schema for bulk update response"""
    updated_count: int
    failed_count: int
    errors: List[dict]  # [{"product_id": "xxx", "error": "Not found"}]
