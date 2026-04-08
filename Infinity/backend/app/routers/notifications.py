from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.notification import (
    MarkReadRequest,
    MarkReadResponse,
    NotificationListResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List notifications with pagination."""
    service = NotificationService(user_id)
    try:
        result = await service.list_notifications(page, limit, unread_only)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        )


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get count of unread notifications."""
    service = NotificationService(user_id)
    try:
        count = await service.get_unread_count()
        return {"count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}",
        )


@router.post("/mark-read", response_model=MarkReadResponse)
async def mark_notifications_read(
    data: MarkReadRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark specific notifications as read."""
    service = NotificationService(user_id)
    try:
        result = await service.mark_as_read(data.notification_ids)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}",
        )


@router.post("/mark-all-read", response_model=MarkReadResponse)
async def mark_all_read(
    user_id: UUID = Depends(get_current_user_id),
):
    """Mark all notifications as read."""
    service = NotificationService(user_id)
    try:
        result = await service.mark_all_as_read()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all as read: {str(e)}",
        )


@router.delete("/{notification_id}", response_model=SuccessMessage)
async def delete_notification(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete a notification."""
    service = NotificationService(user_id)
    try:
        result = await service.delete_notification(notification_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}",
        )
