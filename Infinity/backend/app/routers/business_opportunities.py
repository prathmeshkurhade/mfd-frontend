from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.business_opportunity import (
    BOCreate,
    BOListResponse,
    BOOutcomeUpdate,
    BOPipelineResponse,
    BOResponse,
    BOUpdate,
)
from app.models.common import SuccessMessage
from app.services.bo_service import BOService

router = APIRouter(prefix="/business-opportunities", tags=["Business Opportunities"])


@router.get("/", response_model=BOListResponse)
async def list_opportunities(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    client_id: Optional[UUID] = None,
    lead_id: Optional[UUID] = None,
    opportunity_type: Optional[str] = None,
    stage: Optional[str] = Query(None, description="opportunity_stage filter"),
    outcome: Optional[str] = None,
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List all business opportunities with optional filters and pagination."""
    service = BOService(user_id)
    result = await service.list_opportunities(
        page=page,
        limit=limit,
        client_id=client_id,
        lead_id=lead_id,
        opportunity_type=opportunity_type,
        stage=stage,
        outcome=outcome,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return BOListResponse(**result)


@router.post("/", response_model=BOResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    data: BOCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new business opportunity."""
    service = BOService(user_id)
    try:
        opportunity = await service.create_opportunity(data)
        return BOResponse(**opportunity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create business opportunity: {str(e)}",
        )


@router.get("/pipeline", response_model=BOPipelineResponse)
async def get_pipeline(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get business opportunity pipeline grouped by stage."""
    service = BOService(user_id)
    try:
        pipeline = await service.get_pipeline()
        return pipeline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline: {str(e)}",
        )


@router.get("/{bo_id}", response_model=BOResponse)
async def get_opportunity(
    bo_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get business opportunity by ID."""
    service = BOService(user_id)
    opportunity = await service.get_opportunity(bo_id)
    if not opportunity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business opportunity not found",
        )
    return BOResponse(**opportunity)


@router.put("/{bo_id}", response_model=BOResponse)
async def update_opportunity(
    bo_id: UUID,
    data: BOUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update business opportunity."""
    service = BOService(user_id)
    try:
        opportunity = await service.update_opportunity(bo_id, data)
        return BOResponse(**opportunity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update business opportunity: {str(e)}",
        )


@router.delete("/{bo_id}", response_model=SuccessMessage)
async def delete_opportunity(
    bo_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete business opportunity."""
    service = BOService(user_id)
    try:
        await service.delete_opportunity(bo_id)
        return SuccessMessage(message="Business opportunity deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete business opportunity: {str(e)}",
        )


@router.patch("/{bo_id}/outcome", response_model=BOResponse)
async def update_outcome(
    bo_id: UUID,
    data: BOOutcomeUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update business opportunity outcome."""
    service = BOService(user_id)
    try:
        opportunity = await service.update_outcome(bo_id, data)
        return BOResponse(**opportunity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update outcome: {str(e)}",
        )


@router.patch("/{bo_id}/stage", response_model=BOResponse)
async def update_stage(
    bo_id: UUID,
    stage: str = Query(..., description="New opportunity stage"),
    notes: Optional[str] = Query(None, description="Optional notes"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Update business opportunity stage."""
    service = BOService(user_id)
    try:
        opportunity = await service.update_stage(bo_id, stage, notes)
        return BOResponse(**opportunity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stage: {str(e)}",
        )
