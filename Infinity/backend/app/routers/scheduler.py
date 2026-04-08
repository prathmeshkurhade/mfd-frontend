from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.scheduler import (
    DailyScheduleContent,
    EODContent,
    ProgressContent,
    ScheduledNotificationListResponse,
    ScheduledNotificationResponse,
)
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


@router.get("/daily-schedule", response_model=DailyScheduleContent)
async def get_daily_schedule(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get daily schedule content for morning notification."""
    service = SchedulerService(user_id)
    try:
        content = await service.get_daily_schedule_content()
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily schedule: {str(e)}",
        )


@router.get("/progress", response_model=ProgressContent)
async def get_progress(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get progress content for afternoon notification."""
    service = SchedulerService(user_id)
    try:
        content = await service.get_progress_content()
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}",
        )


@router.get("/eod-summary", response_model=EODContent)
async def get_eod_summary(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get end-of-day summary content."""
    service = SchedulerService(user_id)
    try:
        content = await service.get_eod_content()
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get EOD summary: {str(e)}",
        )


@router.get("/notifications", response_model=ScheduledNotificationListResponse)
async def list_scheduled_notifications(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List scheduled notifications for user."""
    service = SchedulerService(user_id)
    try:
        # Get pending notifications (can be extended to support status filter)
        if status_filter == "pending":
            notifications = await service.get_pending_notifications(channel)
        else:
            # For other statuses, would need to add method to service
            notifications = await service.get_pending_notifications(channel)

        return ScheduledNotificationListResponse(
            notifications=notifications,
            total=len(notifications),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}",
        )


@router.post("/notifications/schedule-today", response_model=SuccessMessage)
async def schedule_today_notifications(
    user_id: UUID = Depends(get_current_user_id),
):
    """Schedule all daily notifications for current user based on profile preferences."""
    service = SchedulerService(user_id)
    try:
        await service.schedule_daily_notifications_for_user()
        return SuccessMessage(
            message="Daily notifications scheduled successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule notifications: {str(e)}",
        )
