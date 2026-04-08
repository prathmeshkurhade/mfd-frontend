from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.constants.enums import ProductCategoryType


class ProductBase(BaseModel):
    """Base schema for master product list"""
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    category: ProductCategoryType
    sub_category: Optional[str] = Field(None, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=255)
    provider_code: Optional[str] = Field(None, max_length=50)
    fund_house: Optional[str] = None
    fund_type: Optional[str] = None  # equity, debt, hybrid, liquid
    fund_sub_type: Optional[str] = None  # large_cap, mid_cap, small_cap
    policy_type: Optional[str] = None  # term, endowment, money_back
    expected_return_rate: Optional[float] = Field(None, ge=0, le=50)
    supports_sip: bool = False
    supports_lumpsum: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a new product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    category: Optional[ProductCategoryType] = None
    sub_category: Optional[str] = Field(None, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=255)
    provider_code: Optional[str] = Field(None, max_length=50)
    fund_house: Optional[str] = None
    fund_type: Optional[str] = None
    fund_sub_type: Optional[str] = None
    policy_type: Optional[str] = None
    expected_return_rate: Optional[float] = Field(None, ge=0, le=50)
    supports_sip: Optional[bool] = None
    supports_lumpsum: Optional[bool] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for product list response"""
    products: List[ProductResponse]
    total: int


class ProductSearchParams(BaseModel):
    """Schema for product search parameters"""
    category: Optional[ProductCategoryType] = None
    provider_name: Optional[str] = None
    fund_type: Optional[str] = None
    supports_sip: Optional[bool] = None
    search: Optional[str] = None  # Search by name
