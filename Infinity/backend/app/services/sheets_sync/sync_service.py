"""
Google Sheets Sync Service
Wrapper service to interact with Supabase Edge Functions for sheet sync.
All data is stored in mfd_profiles and excel_sync_logs tables.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from app.config import settings
from app.database import supabase_admin


class GoogleSheetsSyncService:
    """Service for managing Google Sheets synchronization via Supabase Edge Functions."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.supabase_url = settings.SUPABASE_URL
        self.service_role_key = settings.SUPABASE_SERVICE_KEY

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Check user's Google Sheets sync status from mfd_profiles.

        Returns connection status, sheet info, and last sync time.
        """
        response = (
            supabase_admin.table("mfd_profiles")
            .select(
                "google_connected, google_email, google_sheet_id, "
                "google_drive_folder_id, google_clients_folder_id, "
                "sync_needed, last_synced_at"
            )
            .eq("user_id", str(self.user_id))
            .single()
            .execute()
        )

        if not response.data:
            return {"status": "no_profile", "is_connected": False, "has_sheet": False}

        profile = response.data
        is_connected = bool(profile.get("google_connected"))
        has_sheet = bool(profile.get("google_sheet_id"))

        result: Dict[str, Any] = {
            "status": "ready" if is_connected and has_sheet else "setup_required",
            "is_connected": is_connected,
            "has_sheet": has_sheet,
            "sync_needed": profile.get("sync_needed", False),
            "last_synced_at": profile.get("last_synced_at"),
        }

        if is_connected:
            result["google_email"] = profile.get("google_email")

        if has_sheet:
            sheet_id = profile["google_sheet_id"]
            result["sheet"] = {
                "id": sheet_id,
                "url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
            }

        if profile.get("google_drive_folder_id"):
            result["drive_folder_id"] = profile["google_drive_folder_id"]

        if profile.get("google_clients_folder_id"):
            result["clients_folder_url"] = (
                f"https://drive.google.com/drive/folders/{profile['google_clients_folder_id']}"
            )

        return result

    async def get_oauth_start_url(self) -> str:
        """Get the OAuth start URL that redirects to Google consent screen."""
        return (
            f"{self.supabase_url}/functions/v1/google-oauth-start"
            f"?user_id={self.user_id}"
        )

    async def trigger_sync_to_sheets(self) -> Dict[str, Any]:
        """
        Trigger a full DB → Sheets sync for this user via the
        sync-sheet-snapshot edge function.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.supabase_url}/functions/v1/sync-sheet-snapshot",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "user_id": str(self.user_id),
                    "mode": "on_demand",
                },
            )
            response.raise_for_status()
            return response.json()

    async def trigger_import_from_sheet(self) -> Dict[str, Any]:
        """
        Trigger a Sheet → DB import for this user via the
        import-from-sheet edge function.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.supabase_url}/functions/v1/import-from-sheet",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "user_id": str(self.user_id),
                },
            )
            response.raise_for_status()
            return response.json()

    async def push_record_to_sheet(
        self, table: str, record_id: UUID, row_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Push a single record change to Google Sheets."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.supabase_url}/functions/v1/push-to-sheets",
                headers={
                    "Authorization": f"Bearer {self.service_role_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "id": str(record_id),
                    "userId": str(self.user_id),
                    "table": table,
                    "rowData": row_data,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_sync_history(
        self, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        """Get sync history from excel_sync_logs."""
        response = (
            supabase_admin.table("excel_sync_logs")
            .select("*")
            .eq("user_id", str(self.user_id))
            .order("started_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        count_response = (
            supabase_admin.table("excel_sync_logs")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .execute()
        )

        return {
            "logs": response.data or [],
            "total": count_response.count or 0,
            "limit": limit,
            "offset": offset,
        }

    async def mark_sync_needed(self) -> None:
        """Mark user as needing a sync (dirty flag)."""
        supabase_admin.table("mfd_profiles").update(
            {"sync_needed": True}
        ).eq("user_id", str(self.user_id)).execute()
