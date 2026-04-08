from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.profile import (
    GoogleAuthCallback,
    GoogleAuthURL,
    GoogleConnectResponse,
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get or create MFD profile."""
    service = ProfileService(user_id)
    try:
        # Use get_or_create to ensure profile exists
        profile = await service.get_or_create_profile()
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}",
        )


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: ProfileCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create new MFD profile."""
    service = ProfileService(user_id)
    try:
        profile = await service.create_profile(data)
        return profile
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}",
        )


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update MFD profile."""
    service = ProfileService(user_id)
    try:
        profile = await service.update_profile(data)
        return profile
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}",
        )


@router.get("/google/auth-url", response_model=GoogleAuthURL)
async def get_google_auth_url(
    user_id: UUID = Depends(get_current_user_id),
):
    """Get Google OAuth URL for Drive and Sheets integration."""
    service = ProfileService(user_id)
    try:
        auth_url = await service.generate_google_auth_url()
        return auth_url
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}",
        )


@router.post("/google/callback", response_model=GoogleConnectResponse)
async def google_callback(
    data: GoogleAuthCallback,
    user_id: UUID = Depends(get_current_user_id),
):
    """Handle Google OAuth callback."""
    service = ProfileService(user_id)
    try:
        result = await service.handle_google_callback(data.code, data.state or "")
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect Google account: {str(e)}",
        )


@router.post("/google/disconnect", response_model=SuccessMessage)
async def disconnect_google(
    user_id: UUID = Depends(get_current_user_id),
):
    """Disconnect Google integration."""
    service = ProfileService(user_id)
    try:
        result = await service.disconnect_google()
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect Google: {str(e)}",
        )
