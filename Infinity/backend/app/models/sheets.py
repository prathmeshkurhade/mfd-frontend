"""Pydantic models for Google Sheets sync endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SheetInfo(BaseModel):
    id: str
    url: str


class SyncStatusResponse(BaseModel):
    status: str = Field(
        ..., description="ready | setup_required | no_profile"
    )
    is_connected: bool
    has_sheet: bool
    sync_needed: bool = False
    last_synced_at: Optional[datetime] = None
    google_email: Optional[str] = None
    sheet: Optional[SheetInfo] = None
    drive_folder_id: Optional[str] = None
    clients_folder_url: Optional[str] = None


class SyncTriggerResponse(BaseModel):
    success: bool
    mode: Optional[str] = None
    users_synced: Optional[int] = None
    details: Optional[List[Dict[str, Any]]] = None
    duration_ms: Optional[int] = None


class ImportTriggerResponse(BaseModel):
    success: bool
    leads: Optional[Dict[str, Any]] = None
    clients: Optional[Dict[str, Any]] = None
    business_opportunities: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None


class SyncLogEntry(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    sync_type: Optional[str] = None
    sync_direction: Optional[str] = None
    records_synced: Optional[int] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SyncHistoryResponse(BaseModel):
    logs: List[SyncLogEntry]
    total: int
    limit: int
    offset: int
