from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.device import (
    DeviceListResponse,
    DeviceRegisterRequest,
    DeviceRegisterResponse,
    DeviceTokenRefreshRequest,
    DeviceUnregisterRequest,
)
from app.services.push_notification_service import PushNotificationService

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/register", response_model=DeviceRegisterResponse)
async def register_device(
    data: DeviceRegisterRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Register a new device or update existing device token.
    
    Flutter calls this on login to register the device for push notifications.
    """
    service = PushNotificationService()
    try:
        result = await service.register_device(
            user_id=user_id,
            device_token=data.device_token,
            device_type=data.device_type.value,
            device_name=data.device_name,
            device_model=data.device_model,
            os_version=data.os_version,
            app_version=data.app_version,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device: {str(e)}",
        )


@router.post("/unregister", response_model=DeviceRegisterResponse)
async def unregister_device(
    data: DeviceUnregisterRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Unregister a device (mark as inactive).
    
    Flutter calls this on logout to stop receiving push notifications.
    """
    service = PushNotificationService()
    try:
        result = await service.unregister_device(
            user_id=user_id,
            device_token=data.device_token,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister device: {str(e)}",
        )


@router.post("/refresh-token", response_model=DeviceRegisterResponse)
async def refresh_device_token(
    data: DeviceTokenRefreshRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Refresh device token when it changes.
    
    Flutter calls this when FCM token is refreshed.
    """
    service = PushNotificationService()
    try:
        result = await service.refresh_token(
            user_id=user_id,
            old_token=data.old_token,
            new_token=data.new_token,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh device token: {str(e)}",
        )


@router.get("/", response_model=DeviceListResponse)
async def list_user_devices(
    user_id: UUID = Depends(get_current_user_id),
):
    """
    List all devices registered for the current user.
    
    Returns both active and inactive devices with summary counts.
    """
    service = PushNotificationService()
    try:
        result = await service.get_user_devices_list(user_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list devices: {str(e)}",
        )


@router.delete("/{device_id}", response_model=SuccessMessage)
async def delete_device(
    device_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """
    Delete a specific device.
    
    Permanently removes the device from the database.
    """
    service = PushNotificationService()
    try:
        success = await service.delete_device(user_id, device_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found",
            )
        return SuccessMessage(message="Device deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete device: {str(e)}",
        )
