from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from typing import Optional
from datetime import date
from app.auth.dependencies import get_current_user_id
from app.services.client_product_service import ClientProductService
from app.models.product import ProductResponse, ProductListResponse
from app.models.client_product import (
    ClientProductCreate, ClientProductUpdate, ClientProductResponse,
    ClientProductListResponse, ClientPortfolioSummary, UpdateValueRequest,
    BulkUpdateValueRequest, BulkUpdateValueResponse
)
from app.models.product_transaction import (
    ProductTransactionCreate, ProductTransactionResponse,
    ProductTransactionListResponse, TransactionSummary
)
from app.models.common import SuccessMessage

router = APIRouter(prefix="/client-products", tags=["Client Products"])


# ==================== MASTER PRODUCTS ====================

@router.get("/products/master", response_model=ProductListResponse)
async def list_master_products(
    category: Optional[str] = Query(None, description="Filter by product category"),
    provider_name: Optional[str] = Query(None, description="Filter by provider name"),
    fund_type: Optional[str] = Query(None, description="Filter by fund type"),
    supports_sip: Optional[bool] = Query(None, description="Filter by SIP support"),
    search: Optional[str] = Query(None, description="Search by product name"),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get master list of available products"""
    service = ClientProductService(user_id)
    return await service.list_master_products(
        category=category,
        provider_name=provider_name,
        fund_type=fund_type,
        supports_sip=supports_sip,
        search=search
    )


@router.get("/products/master/{product_id}", response_model=ProductResponse)
async def get_master_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get a single master product by ID"""
    service = ClientProductService(user_id)
    product = await service.get_master_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


# ==================== CLIENT PRODUCTS ====================

@router.get("/client/{client_id}", response_model=ClientProductListResponse)
async def get_client_products(
    client_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    status: str = Query("active", description="Filter by status"),
    investment_type: Optional[str] = Query(None, description="Filter by investment type"),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get all products for a client"""
    service = ClientProductService(user_id)
    return await service.get_client_products(
        client_id=client_id,
        category=category,
        status=status,
        investment_type=investment_type
    )


@router.post("/", response_model=ClientProductResponse, status_code=status.HTTP_201_CREATED)
async def add_client_product(
    data: ClientProductCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    """Add a product to client's portfolio"""
    service = ClientProductService(user_id)
    try:
        return await service.add_client_product(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{product_id}", response_model=ClientProductResponse)
async def get_client_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get a single client product by ID"""
    service = ClientProductService(user_id)
    product = await service.get_client_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.put("/{product_id}", response_model=ClientProductResponse)
async def update_client_product(
    product_id: UUID,
    data: ClientProductUpdate,
    user_id: UUID = Depends(get_current_user_id)
):
    """Update a client product"""
    service = ClientProductService(user_id)
    try:
        return await service.update_client_product(product_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{product_id}/value", response_model=ClientProductResponse)
async def update_product_value(
    product_id: UUID,
    data: UpdateValueRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """Quick update for current value/NAV"""
    service = ClientProductService(user_id)
    try:
        return await service.update_product_value(product_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{product_id}", response_model=SuccessMessage)
async def delete_client_product(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Delete a client product"""
    service = ClientProductService(user_id)
    try:
        return await service.delete_client_product(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/client/{client_id}/portfolio", response_model=ClientPortfolioSummary)
async def get_portfolio_summary(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get portfolio summary with category breakdown"""
    service = ClientProductService(user_id)
    try:
        return await service.get_portfolio_summary(client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/bulk-update-values", response_model=BulkUpdateValueResponse)
async def bulk_update_values(
    data: BulkUpdateValueRequest,
    user_id: UUID = Depends(get_current_user_id)
):
    """Update multiple product values at once (for NAV updates)"""
    service = ClientProductService(user_id)
    return await service.bulk_update_values(data)


# ==================== TRANSACTIONS ====================

@router.post("/{product_id}/transactions", response_model=ProductTransactionResponse, status_code=status.HTTP_201_CREATED)
async def add_transaction(
    product_id: UUID,
    data: ProductTransactionCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    """Add a transaction for a client product"""
    # Override client_product_id with path parameter
    data.client_product_id = product_id
    
    service = ClientProductService(user_id)
    try:
        return await service.add_transaction(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{product_id}/transactions", response_model=ProductTransactionListResponse)
async def get_transactions(
    product_id: UUID,
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get all transactions for a client product"""
    service = ClientProductService(user_id)
    try:
        return await service.get_transactions(
            client_product_id=product_id,
            transaction_type=transaction_type,
            date_from=date_from,
            date_to=date_to
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{product_id}/transactions/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    product_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """Get transaction summary for a client product"""
    service = ClientProductService(user_id)
    try:
        return await service.get_transaction_summary(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
