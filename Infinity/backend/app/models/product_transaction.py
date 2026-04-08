from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.constants.enums import TransactionTypeEnum


class ProductTransactionCreate(BaseModel):
    """Schema for creating a product transaction"""
    client_product_id: UUID
    transaction_type: TransactionTypeEnum
    transaction_date: date
    amount: float = Field(..., gt=0)
    units: Optional[float] = Field(None, ge=0)
    nav: Optional[float] = Field(None, ge=0)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class ProductTransactionResponse(BaseModel):
    """Schema for product transaction response"""
    id: UUID
    user_id: UUID
    client_product_id: UUID
    transaction_type: TransactionTypeEnum
    transaction_date: date
    amount: float
    units: Optional[float]
    nav: Optional[float]
    reference_number: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductTransactionListResponse(BaseModel):
    """Schema for product transaction list response with aggregates"""
    transactions: List[ProductTransactionResponse]
    total: int
    total_invested: float  # Sum of purchases
    total_redeemed: float  # Sum of redemptions
    net_investment: float  # invested - redeemed


class TransactionSummary(BaseModel):
    """Schema for transaction summary statistics"""
    client_product_id: UUID
    product_name: str
    total_transactions: int
    first_transaction_date: date
    last_transaction_date: date
    total_invested: float
    total_redeemed: float
    sip_installments_count: int
