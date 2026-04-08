"""
Sheets Sync Router — endpoints for Google Sheets sync operations.

All heavy lifting is done by Supabase Edge Functions;
this router is a thin proxy that authenticates the user and delegates.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.sheets import (
    ImportTriggerResponse,
    SyncHistoryResponse,
    SyncStatusResponse,
    SyncTriggerResponse,
)
from app.services.sheets_sync.sync_service import GoogleSheetsSyncService

router = APIRouter(prefix="/sheets", tags=["Sheets Sync"])


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    user_id: UUID = Depends(get_current_user_id),
):
    """Check Google Sheets sync status for the current user."""
    service = GoogleSheetsSyncService(user_id)
    try:
        return await service.get_sync_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {e}",
        )


@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_sync_to_sheets(
    user_id: UUID = Depends(get_current_user_id),
):
    """Trigger a full DB → Google Sheets sync (push all data to sheet)."""
    service = GoogleSheetsSyncService(user_id)

    sync_status = await service.get_sync_status()
    if sync_status.get("status") != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Sheets not set up. Please connect Google first.",
        )

    try:
        result = await service.trigger_sync_to_sheets()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Sync failed: {e}",
        )


@router.post("/import", response_model=ImportTriggerResponse)
async def trigger_import_from_sheet(
    user_id: UUID = Depends(get_current_user_id),
):
    """Trigger a Sheet → DB import (pull data from sheet into database)."""
    service = GoogleSheetsSyncService(user_id)

    sync_status = await service.get_sync_status()
    if sync_status.get("status") != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Sheets not set up. Please connect Google first.",
        )

    try:
        result = await service.trigger_import_from_sheet()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Import failed: {e}",
        )


@router.get("/history", response_model=SyncHistoryResponse)
async def get_sync_history(
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Get sync history / logs for the current user."""
    service = GoogleSheetsSyncService(user_id)
    try:
        return await service.get_sync_history(limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync history: {e}",
        )


@router.post("/mark-dirty")
async def mark_sync_needed(
    user_id: UUID = Depends(get_current_user_id),
):
    """Manually mark user data as needing sync (sets sync_needed flag)."""
    service = GoogleSheetsSyncService(user_id)
    try:
        await service.mark_sync_needed()
        return {"message": "Sync flag set. Data will be synced on next cron cycle."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark sync needed: {e}",
        )
