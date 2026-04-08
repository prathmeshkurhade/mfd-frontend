from datetime import date
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get comprehensive dashboard statistics."""
    service = DashboardService(user_id)
    try:
        stats = await service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}",
        )


@router.get("/today", response_model=Dict[str, Any])
async def get_today_summary(
    target_date: date = Query(None, description="Date to get summary for (defaults to today)"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get summary for a given date with pending tasks, leads, touchpoints, and birthdays."""
    service = DashboardService(user_id)
    try:
        summary = await service.get_today_summary(target_date)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's summary: {str(e)}",
        )


@router.get("/calendar-events", response_model=List[Dict[str, Any]])
async def get_calendar_events(
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get all calendar events (tasks, touchpoints, leads, opportunities) for a date range."""
    service = DashboardService(user_id)
    try:
        events = await service.get_calendar_events(date_from, date_to)
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get calendar events: {str(e)}",
        )


@router.get("/pipeline", response_model=Dict[str, Any])
async def get_pipeline_summary(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get business opportunity pipeline summary."""
    service = DashboardService(user_id)
    try:
        pipeline = await service.get_pipeline_summary()
        return pipeline
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pipeline summary: {str(e)}",
        )


@router.get("/conversions", response_model=Dict[str, Any])
async def get_conversion_stats(
    period: str = Query("month", description="Period: month, quarter, or year"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get lead conversion statistics."""
    service = DashboardService(user_id)
    try:
        stats = await service.get_conversion_stats(period)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversion stats: {str(e)}",
        )


@router.get("/growth", response_model=List[Dict[str, Any]])
async def get_client_growth(
    period: str = Query("year", description="Period: month, quarter, or year"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Get client growth data by month."""
    service = DashboardService(user_id)
    try:
        growth = await service.get_client_growth(period)
        return growth
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client growth: {str(e)}",
        )
