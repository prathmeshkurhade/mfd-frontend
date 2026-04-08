from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.campaign import (
    CampaignCreate,
    CampaignExecuteResponse,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdate,
)
from app.models.common import SuccessMessage
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List campaigns with pagination."""
    service = CampaignService(user_id)
    try:
        result = await service.list_campaigns(page, limit)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list campaigns: {str(e)}",
        )


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new campaign."""
    service = CampaignService(user_id)
    try:
        campaign = await service.create_campaign(data)
        return campaign
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}",
        )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific campaign."""
    service = CampaignService(user_id)
    try:
        campaign = await service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )
        return campaign
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign: {str(e)}",
        )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update a campaign (only if not executed)."""
    service = CampaignService(user_id)
    try:
        campaign = await service.update_campaign(campaign_id, data)
        return campaign
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update campaign: {str(e)}",
        )


@router.delete("/{campaign_id}", response_model=SuccessMessage)
async def delete_campaign(
    campaign_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete a campaign (only if not executed)."""
    service = CampaignService(user_id)
    try:
        result = await service.delete_campaign(campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete campaign: {str(e)}",
        )


@router.get("/{campaign_id}/preview", response_model=Dict[str, Any])
async def preview_campaign(
    campaign_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Preview campaign with sample recipients and message."""
    service = CampaignService(user_id)
    try:
        preview = await service.preview_campaign(campaign_id)
        return preview
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview campaign: {str(e)}",
        )


@router.post("/{campaign_id}/execute", response_model=CampaignExecuteResponse)
async def execute_campaign(
    campaign_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Execute campaign and send to all recipients."""
    service = CampaignService(user_id)
    try:
        result = await service.execute_campaign(campaign_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute campaign: {str(e)}",
        )


@router.get("/birthdays/today", response_model=List[Dict[str, Any]])
async def get_today_birthdays(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get clients with birthdays today."""
    service = CampaignService(user_id)
    try:
        clients = await service.get_birthday_clients_today()
        return clients
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get birthday clients: {str(e)}",
        )
