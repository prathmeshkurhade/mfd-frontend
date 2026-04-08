from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.lead import (
    LeadCreate,
    LeadListResponse,
    LeadResponse,
    LeadStatusUpdate,
    LeadUpdate,
)
from app.models.common import SuccessMessage
from app.services.lead_service import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=LeadListResponse)
async def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all leads with optional filters and pagination."""
    service = LeadService(user_id)
    result = await service.list_leads(
        page=page,
        limit=limit,
        search=search,
        status=status,
        source=source,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return LeadListResponse(**result)


@router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    data: LeadCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new lead."""
    service = LeadService(user_id)
    try:
        lead = await service.create_lead(data)
        return LeadResponse(**lead)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lead: {str(e)}",
        )


@router.get("/today-followups", response_model=List[LeadResponse])
async def get_today_followups(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get today's follow-up leads."""
    service = LeadService(user_id)
    leads = await service.get_today_followups()
    return [LeadResponse(**lead) for lead in leads]


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get lead by ID."""
    service = LeadService(user_id)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return LeadResponse(**lead)


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update lead."""
    service = LeadService(user_id)
    try:
        lead = await service.update_lead(lead_id, data)
        return LeadResponse(**lead)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead: {str(e)}",
        )


@router.delete("/{lead_id}", response_model=SuccessMessage)
async def delete_lead(
    lead_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete lead."""
    service = LeadService(user_id)
    try:
        await service.delete_lead(lead_id)
        return SuccessMessage(message="Lead deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{lead_id}/status", response_model=LeadResponse)
async def update_lead_status(
    lead_id: UUID,
    data: LeadStatusUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update lead status."""
    service = LeadService(user_id)
    try:
        lead = await service.update_status(lead_id, data)
        return LeadResponse(**lead)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lead status: {str(e)}",
        )
