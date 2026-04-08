"""Profile Service for MFD profile management."""

from typing import Optional
from uuid import UUID

from app.config import settings
from app.database import supabase
from app.models.common import SuccessMessage
from app.models.profile import (
    GoogleAuthURL,
    GoogleConnectResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)


class ProfileService:
    """Service for managing MFD profile."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def get_profile(self) -> Optional[ProfileResponse]:
        """Get MFD profile by user_id."""
        response = (
            supabase.table("mfd_profiles")
            .select("*")
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            return None

        profile = response.data[0]
        return ProfileResponse(**profile)

    async def create_profile(self, data: ProfileCreate) -> ProfileResponse:
        """Create new MFD profile."""
        profile_data = {
            "user_id": str(self.user_id),
            **data.model_dump(mode="json", exclude_unset=True),
        }

        response = supabase.table("mfd_profiles").insert(profile_data).execute()

        if not response.data:
            raise Exception("Failed to create profile")

        return ProfileResponse(**response.data[0])

    async def update_profile(self, data: ProfileUpdate) -> ProfileResponse:
        """Update MFD profile."""
        update_data = data.model_dump(mode="json", exclude_unset=True)

        if not update_data:
            raise ValueError("No fields to update")

        # Get existing columns from DB to avoid sending fields that don't exist
        existing = (
            supabase.table("mfd_profiles")
            .select("*")
            .eq("user_id", str(self.user_id))
            .limit(1)
            .execute()
        )
        if existing.data:
            valid_columns = set(existing.data[0].keys())
            update_data = {k: v for k, v in update_data.items() if k in valid_columns}

        if not update_data:
            raise ValueError("No valid fields to update")

        response = (
            supabase.table("mfd_profiles")
            .update(update_data)
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            raise ValueError("Profile not found")

        return ProfileResponse(**response.data[0])

    async def get_or_create_profile(self) -> ProfileResponse:
        """Get existing profile or create default one."""
        # Try to get existing profile
        profile = await self.get_profile()

        if profile:
            return profile

        # Create default profile
        default_data = ProfileCreate(
            name="MFD User",
            phone="+910000000000",  # Placeholder
            num_employees=0,
            eod_time="18:00",
        )

        return await self.create_profile(default_data)

    async def generate_google_auth_url(self) -> GoogleAuthURL:
        """
        Return the Supabase Edge Function URL that handles the full OAuth flow.
        The edge function redirects to Google, exchanges tokens, creates
        the Drive folder + Sheet, and updates mfd_profiles automatically.
        """
        supabase_url = settings.SUPABASE_URL
        if not supabase_url:
            raise ValueError(
                "SUPABASE_URL not configured. Cannot generate Google auth URL."
            )

        auth_url = (
            f"{supabase_url}/functions/v1/google-oauth-start"
            f"?user_id={self.user_id}"
        )

        return GoogleAuthURL(auth_url=auth_url)

    async def handle_google_callback(
        self, code: str, state: str
    ) -> GoogleConnectResponse:
        """
        Verify Google OAuth status after the edge function callback completes.
        The actual OAuth flow (token exchange, folder/sheet creation) is handled
        entirely by the google-oauth-callback Supabase Edge Function.
        This endpoint lets the mobile app confirm the connection succeeded.
        """
        response = (
            supabase.table("mfd_profiles")
            .select(
                "google_connected, google_email, "
                "google_drive_folder_id, google_sheet_id"
            )
            .eq("user_id", str(self.user_id))
            .single()
            .execute()
        )

        if not response.data:
            raise ValueError("Profile not found")

        profile = response.data

        if not profile.get("google_connected"):
            raise ValueError(
                "Google account not yet connected. "
                "Please complete the OAuth flow first."
            )

        return GoogleConnectResponse(
            message="Google account connected successfully",
            google_email=profile.get("google_email"),
            drive_folder_id=profile.get("google_drive_folder_id"),
            sheet_id=profile.get("google_sheet_id"),
        )

    async def disconnect_google(self) -> SuccessMessage:
        """Disconnect Google integration."""
        update_data = {
            "google_connected": False,
            "google_email": None,
            "google_access_token": None,
            "google_refresh_token": None,
            "google_token_expiry": None,
            "google_drive_folder_id": None,
            "google_sheet_id": None,
            "google_clients_folder_id": None,
        }

        response = (
            supabase.table("mfd_profiles")
            .update(update_data)
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            raise ValueError("Profile not found")

        return SuccessMessage(message="Google account disconnected successfully")
