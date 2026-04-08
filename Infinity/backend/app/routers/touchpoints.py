from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.touchpoint import (
    ClientTouchpointStats,
    MOMResponse,
    MOMUpdate,
    TouchpointComplete,
    TouchpointListResponse,
    TouchpointResponse,
    TouchpointCreate,
    TouchpointUpdate,
)
from app.services.touchpoint_service import TouchpointService

router = APIRouter(prefix="/touchpoints", tags=["Touchpoints"])


@router.get("/", response_model=TouchpointListResponse)
async def list_touchpoints(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    client_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    status: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: str = Query("scheduled_date", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all touchpoints with optional filters and pagination."""
    service = TouchpointService(user_id)
    result = await service.list_touchpoints(
        page=page,
        limit=limit,
        client_id=client_id,
        lead_id=lead_id,
        status=status,
        interaction_type=interaction_type,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TouchpointListResponse(**result)


@router.post("/", response_model=TouchpointResponse, status_code=status.HTTP_201_CREATED)
async def create_touchpoint(
    data: TouchpointCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new touchpoint."""
    service = TouchpointService(user_id)
    try:
        touchpoint = await service.create_touchpoint(data)
        return TouchpointResponse(**touchpoint)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create touchpoint: {str(e)}",
        )


@router.get("/upcoming", response_model=List[TouchpointResponse])
async def get_upcoming_touchpoints(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get upcoming touchpoints."""
    service = TouchpointService(user_id)
    touchpoints = await service.get_upcoming()
    return [TouchpointResponse(**tp) for tp in touchpoints]


@router.get("/{touchpoint_id}", response_model=TouchpointResponse)
async def get_touchpoint(
    touchpoint_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get touchpoint by ID."""
    service = TouchpointService(user_id)
    touchpoint = await service.get_touchpoint(touchpoint_id)
    if not touchpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Touchpoint not found",
        )
    return TouchpointResponse(**touchpoint)


@router.put("/{touchpoint_id}", response_model=TouchpointResponse)
async def update_touchpoint(
    touchpoint_id: UUID,
    data: TouchpointUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update touchpoint."""
    service = TouchpointService(user_id)
    try:
        touchpoint = await service.update_touchpoint(touchpoint_id, data)
        return TouchpointResponse(**touchpoint)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update touchpoint: {str(e)}",
        )


@router.delete("/{touchpoint_id}", response_model=SuccessMessage)
async def delete_touchpoint(
    touchpoint_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete touchpoint."""
    service = TouchpointService(user_id)
    try:
        await service.delete_touchpoint(touchpoint_id)
        return SuccessMessage(message="Touchpoint deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete touchpoint: {str(e)}",
        )


@router.post("/{touchpoint_id}/complete", response_model=TouchpointResponse)
async def complete_touchpoint(
    touchpoint_id: UUID,
    data: TouchpointComplete,
    user_id: UUID = Depends(get_current_user_id),
):
    """Complete touchpoint."""
    service = TouchpointService(user_id)
    try:
        touchpoint = await service.complete_touchpoint(touchpoint_id, data)
        return TouchpointResponse(**touchpoint)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete touchpoint: {str(e)}",
        )


@router.put("/{touchpoint_id}/mom", response_model=MOMResponse)
async def update_mom(
    touchpoint_id: UUID,
    data: MOMUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update MoM text."""
    service = TouchpointService(user_id)
    try:
        mom_response = await service.update_mom(touchpoint_id, data)
        return mom_response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update MoM: {str(e)}",
        )


@router.post("/{touchpoint_id}/reschedule", response_model=TouchpointResponse)
async def reschedule(
    touchpoint_id: UUID,
    new_date: date = Query(..., description="New scheduled date"),
    new_time: Optional[str] = Query(None, description="New scheduled time (HH:MM)"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Reschedule touchpoint."""
    service = TouchpointService(user_id)
    try:
        touchpoint = await service.reschedule(touchpoint_id, new_date, new_time)
        return TouchpointResponse(**touchpoint)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reschedule touchpoint: {str(e)}",
        )


@router.get("/client/{client_id}", response_model=ClientTouchpointStats)
async def get_client_touchpoints(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get all touchpoints for a client with stats."""
    service = TouchpointService(user_id)
    try:
        stats = await service.get_client_touchpoints(client_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client touchpoints: {str(e)}",
        )
