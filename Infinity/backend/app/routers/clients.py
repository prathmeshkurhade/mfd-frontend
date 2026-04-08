from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.client import (
    ClientCreate,
    ClientListResponse,
    ClientOverview,
    ClientResponse,
    ClientUpdate,
    ConvertLeadRequest,
    DuplicateCheckResponse,
)
from app.models.common import SuccessMessage
from app.services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=ClientListResponse)
async def list_clients(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    area: Optional[str] = None,
    age_group: Optional[str] = None,
    risk_profile: Optional[str] = None,
    sort_by: str = Query("name", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all clients with optional filters and pagination."""
    service = ClientService(user_id)
    result = await service.list_clients(
        page=page,
        limit=limit,
        search=search,
        area=area,
        age_group=age_group,
        risk_profile=risk_profile,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return ClientListResponse(**result)


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new client."""
    service = ClientService(user_id)
    try:
        client = await service.create_client(data)
        return ClientResponse(**client)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get client by ID."""
    service = ClientService(user_id)
    client = await service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return ClientResponse(**client)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update client."""
    service = ClientService(user_id)
    try:
        client = await service.update_client(client_id, data)
        return ClientResponse(**client)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}",
        )


@router.delete("/{client_id}", response_model=SuccessMessage)
async def delete_client(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete client (soft delete)."""
    service = ClientService(user_id)
    try:
        await service.delete_client(client_id)
        return SuccessMessage(message="Client deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{client_id}/overview", response_model=ClientOverview)
async def get_client_overview(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get client overview with related data."""
    service = ClientService(user_id)
    try:
        overview = await service.get_overview(client_id)
        return ClientOverview(**overview)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(
    phone: str = Query(..., description="Phone number to check"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Check if client with phone number already exists."""
    service = ClientService(user_id)
    result = await service.check_duplicate(phone)
    return DuplicateCheckResponse(**result)


@router.post("/convert-from-lead", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def convert_lead_to_client(
    data: ConvertLeadRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Convert a lead to a client."""
    service = ClientService(user_id)
    try:
        client = await service.convert_from_lead(
            lead_id=data.lead_id,
            birthdate=data.birthdate,
            email=data.email,
            address=data.address,
            risk_profile=data.risk_profile.value if data.risk_profile else None,
        )
        return ClientResponse(**client)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert lead: {str(e)}",
        )


@router.get("/{client_id}/cash-flow")
async def get_cash_flow(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get client cash flow data."""
    service = ClientService(user_id)
    # Verify client exists
    client = await service.get_client(client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    
    cash_flow = await service.get_cash_flow(client_id)
    if not cash_flow:
        return {
            "client_id": str(client_id),
            "insurance_premiums": {},
            "savings": {},
            "loans": {},
            "expenses": {},
            "income": {},
            "current_investments": {},
            "total_income_yearly": 0,
            "total_expenses_yearly": 0,
            "total_pending_loans": 0,
            "cash_surplus_yearly": 0,
            "cash_surplus_monthly": 0,
        }
    return cash_flow


@router.put("/{client_id}/cash-flow")
async def update_cash_flow(
    client_id: UUID,
    data: Dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
):
    """Update client cash flow data."""
    service = ClientService(user_id)
    try:
        cash_flow = await service.update_cash_flow(client_id, data)
        return cash_flow
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update cash flow: {str(e)}",
        )
