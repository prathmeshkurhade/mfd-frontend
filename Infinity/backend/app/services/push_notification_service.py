"""Push Notification Service for Firebase Cloud Messaging."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import httpx

from app.config import settings
from app.database import supabase
from app.models.device import (
    DeviceListResponse,
    DeviceRegisterResponse,
    DeviceResponse,
    PushNotificationResponse,
)

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for managing push notifications via Firebase Cloud Messaging."""

    FCM_API_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self):
        self.fcm_server_key = settings.FCM_SERVER_KEY
        self.fcm_sender_id = settings.FCM_SENDER_ID

    def _is_fcm_configured(self) -> bool:
        """Check if FCM is properly configured."""
        return bool(self.fcm_server_key and self.fcm_sender_id)

    async def send_push_notification(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Optional[dict] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[UUID] = None,
    ) -> PushNotificationResponse:
        """
        Send push notification to all active devices of a user.
        
        Args:
            user_id: UUID of the user to send notification to
            title: Notification title
            body: Notification body
            data: Optional additional data payload
            related_entity_type: Optional type of related entity (e.g., "task", "touchpoint")
            related_entity_id: Optional UUID of related entity
            
        Returns:
            PushNotificationResponse with send results
        """
        if not self._is_fcm_configured():
            logger.warning("FCM is not configured. Skipping push notification.")
            return PushNotificationResponse(
                success=False,
                message="FCM not configured",
                devices_sent=0,
                devices_failed=0,
            )

        # Get user's active devices
        devices = await self.get_user_devices(user_id, active_only=True)
        
        if not devices:
            logger.info(f"No active devices found for user {user_id}")
            return PushNotificationResponse(
                success=True,
                message="No active devices to send to",
                devices_sent=0,
                devices_failed=0,
            )

        # Prepare notification payload
        notification_data = data or {}
        if related_entity_type:
            notification_data["related_entity_type"] = related_entity_type
        if related_entity_id:
            notification_data["related_entity_id"] = str(related_entity_id)

        # Send to all devices
        sent_count = 0
        failed_count = 0
        invalid_tokens = []

        for device in devices:
            try:
                success = await self.send_push_to_token(
                    device.device_token,
                    title,
                    body,
                    notification_data,
                )
                if success:
                    sent_count += 1
                    # Update last_used_at
                    await self._update_device_last_used(device.id)
                else:
                    failed_count += 1
                    invalid_tokens.append(device.device_token)
            except Exception as e:
                logger.error(f"Failed to send push to device {device.id}: {str(e)}")
                failed_count += 1
                invalid_tokens.append(device.device_token)

        # Cleanup invalid tokens
        if invalid_tokens:
            await self.cleanup_invalid_tokens(invalid_tokens)

        return PushNotificationResponse(
            success=sent_count > 0,
            message=f"Sent to {sent_count} device(s), failed on {failed_count}",
            devices_sent=sent_count,
            devices_failed=failed_count,
        )

    async def send_push_to_token(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Send push notification to a specific device token.
        
        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional additional data payload
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._is_fcm_configured():
            logger.warning("FCM is not configured. Skipping push notification.")
            return False

        headers = {
            "Authorization": f"key={self.fcm_server_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "to": device_token,
            "notification": {
                "title": title,
                "body": body,
            },
            "priority": "high",
        }

        if data:
            payload["data"] = data

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.FCM_API_URL,
                    json=payload,
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") == 1:
                        logger.info(f"Push notification sent successfully to token {device_token[:20]}...")
                        return True
                    else:
                        logger.warning(f"FCM returned failure for token {device_token[:20]}...")
                        return False
                else:
                    logger.error(f"FCM API returned status {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False

    async def register_device(
        self,
        user_id: UUID,
        device_token: str,
        device_type: str,
        device_name: Optional[str] = None,
        device_model: Optional[str] = None,
        os_version: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> DeviceRegisterResponse:
        """
        Register a new device or update existing device token.
        
        Args:
            user_id: UUID of the user
            device_token: FCM device token
            device_type: Type of device (android, ios, web)
            device_name: Optional device name
            device_model: Optional device model
            os_version: Optional OS version
            app_version: Optional app version
            
        Returns:
            DeviceRegisterResponse with registration result
        """
        try:
            # Check if device token already exists for this user
            existing = (
                supabase.table("devices")
                .select("*")
                .eq("user_id", str(user_id))
                .eq("device_token", device_token)
                .execute()
            )

            device_data = {
                "user_id": str(user_id),
                "device_token": device_token,
                "device_type": device_type,
                "device_name": device_name,
                "device_model": device_model,
                "os_version": os_version,
                "app_version": app_version,
                "is_active": True,
                "last_used_at": datetime.now().isoformat(),
            }

            if existing.data:
                # Update existing device
                response = (
                    supabase.table("devices")
                    .update(device_data)
                    .eq("id", existing.data[0]["id"])
                    .execute()
                )
                device_id = existing.data[0]["id"]
                message = "Device updated successfully"
            else:
                # Insert new device
                response = supabase.table("devices").insert(device_data).execute()
                device_id = response.data[0]["id"] if response.data else None
                message = "Device registered successfully"

            if not response.data:
                raise Exception("Failed to register device")

            return DeviceRegisterResponse(
                success=True,
                message=message,
                device_id=UUID(device_id),
            )

        except Exception as e:
            logger.error(f"Error registering device: {str(e)}")
            return DeviceRegisterResponse(
                success=False,
                message=f"Failed to register device: {str(e)}",
                device_id=None,
            )

    async def unregister_device(
        self,
        user_id: UUID,
        device_token: str,
    ) -> DeviceRegisterResponse:
        """
        Unregister a device (mark as inactive).
        
        Args:
            user_id: UUID of the user
            device_token: FCM device token to unregister
            
        Returns:
            DeviceRegisterResponse with unregister result
        """
        try:
            response = (
                supabase.table("devices")
                .update({"is_active": False})
                .eq("user_id", str(user_id))
                .eq("device_token", device_token)
                .execute()
            )

            if not response.data:
                return DeviceRegisterResponse(
                    success=False,
                    message="Device not found",
                    device_id=None,
                )

            return DeviceRegisterResponse(
                success=True,
                message="Device unregistered successfully",
                device_id=UUID(response.data[0]["id"]),
            )

        except Exception as e:
            logger.error(f"Error unregistering device: {str(e)}")
            return DeviceRegisterResponse(
                success=False,
                message=f"Failed to unregister device: {str(e)}",
                device_id=None,
            )

    async def refresh_token(
        self,
        user_id: UUID,
        old_token: str,
        new_token: str,
    ) -> DeviceRegisterResponse:
        """
        Refresh device token when it changes.
        
        Args:
            user_id: UUID of the user
            old_token: Old FCM device token
            new_token: New FCM device token
            
        Returns:
            DeviceRegisterResponse with refresh result
        """
        try:
            response = (
                supabase.table("devices")
                .update({
                    "device_token": new_token,
                    "last_used_at": datetime.now().isoformat(),
                })
                .eq("user_id", str(user_id))
                .eq("device_token", old_token)
                .execute()
            )

            if not response.data:
                return DeviceRegisterResponse(
                    success=False,
                    message="Device not found with old token",
                    device_id=None,
                )

            return DeviceRegisterResponse(
                success=True,
                message="Device token refreshed successfully",
                device_id=UUID(response.data[0]["id"]),
            )

        except Exception as e:
            logger.error(f"Error refreshing device token: {str(e)}")
            return DeviceRegisterResponse(
                success=False,
                message=f"Failed to refresh device token: {str(e)}",
                device_id=None,
            )

    async def get_user_devices(
        self,
        user_id: UUID,
        active_only: bool = True,
    ) -> List[DeviceResponse]:
        """
        Get all devices for a user.
        
        Args:
            user_id: UUID of the user
            active_only: If True, only return active devices
            
        Returns:
            List of DeviceResponse objects
        """
        try:
            query = supabase.table("devices").select("*").eq("user_id", str(user_id))

            if active_only:
                query = query.eq("is_active", True)

            response = query.order("last_used_at", desc=True).execute()

            if not response.data:
                return []

            return [DeviceResponse(**device) for device in response.data]

        except Exception as e:
            logger.error(f"Error getting user devices: {str(e)}")
            return []

    async def get_user_devices_list(
        self,
        user_id: UUID,
    ) -> DeviceListResponse:
        """
        Get all devices for a user with summary counts.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            DeviceListResponse with devices and counts
        """
        try:
            all_devices = await self.get_user_devices(user_id, active_only=False)
            active_devices = [d for d in all_devices if d.is_active]

            return DeviceListResponse(
                devices=all_devices,
                total=len(all_devices),
                active_count=len(active_devices),
            )

        except Exception as e:
            logger.error(f"Error getting user devices list: {str(e)}")
            return DeviceListResponse(devices=[], total=0, active_count=0)

    async def cleanup_invalid_tokens(
        self,
        invalid_tokens: List[str],
    ) -> int:
        """
        Mark devices with invalid tokens as inactive.
        
        Args:
            invalid_tokens: List of invalid FCM tokens
            
        Returns:
            Number of devices marked as inactive
        """
        if not invalid_tokens:
            return 0

        try:
            response = (
                supabase.table("devices")
                .update({"is_active": False})
                .in_("device_token", invalid_tokens)
                .execute()
            )

            cleaned_count = len(response.data) if response.data else 0
            logger.info(f"Cleaned up {cleaned_count} invalid device tokens")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up invalid tokens: {str(e)}")
            return 0

    async def delete_device(
        self,
        user_id: UUID,
        device_id: UUID,
    ) -> bool:
        """
        Delete a specific device.
        
        Args:
            user_id: UUID of the user
            device_id: UUID of the device to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = (
                supabase.table("devices")
                .delete()
                .eq("id", str(device_id))
                .eq("user_id", str(user_id))
                .execute()
            )

            return bool(response.data)

        except Exception as e:
            logger.error(f"Error deleting device: {str(e)}")
            return False

    async def _update_device_last_used(self, device_id: UUID) -> None:
        """Update the last_used_at timestamp for a device."""
        try:
            supabase.table("devices").update({
                "last_used_at": datetime.now().isoformat(),
            }).eq("id", str(device_id)).execute()
        except Exception as e:
            logger.error(f"Error updating device last_used_at: {str(e)}")
