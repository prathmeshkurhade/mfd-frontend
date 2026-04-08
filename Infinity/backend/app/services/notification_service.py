"""Notification Service for user notifications."""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.database import supabase
from app.models.common import SuccessMessage
from app.models.notification import (
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_notifications(
        self, page: int = 1, limit: int = 20, unread_only: bool = False
    ) -> NotificationListResponse:
        """List notifications for user."""
        offset = (page - 1) * limit

        query = (
            supabase.table("notifications")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        if unread_only:
            query = query.eq("is_read", False)

        response = (
            query.order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        notifications = (
            [NotificationResponse(**notif) for notif in response.data]
            if response.data
            else []
        )

        total = response.count if response.count is not None else 0
        unread_count = await self.get_unread_count()

        return NotificationListResponse(
            notifications=notifications,
            total=total,
            unread_count=unread_count,
        )

    async def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        response = (
            supabase.table("notifications")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("is_read", False)
            .execute()
        )

        return response.count if response.count is not None else 0

    async def mark_as_read(self, notification_ids: List[UUID]) -> MarkReadResponse:
        """Mark specific notifications as read."""
        if not notification_ids:
            return MarkReadResponse(marked_count=0, message="No notifications to mark")

        id_strings = [str(nid) for nid in notification_ids]

        update_data = {
            "is_read": True,
            "read_at": datetime.now().isoformat(),
        }

        response = (
            supabase.table("notifications")
            .update(update_data)
            .eq("user_id", str(self.user_id))
            .in_("id", id_strings)
            .execute()
        )

        marked_count = len(response.data) if response.data else 0

        return MarkReadResponse(
            marked_count=marked_count,
            message=f"Marked {marked_count} notification(s) as read",
        )

    async def mark_all_as_read(self) -> MarkReadResponse:
        """Mark all unread notifications as read."""
        update_data = {
            "is_read": True,
            "read_at": datetime.now().isoformat(),
        }

        response = (
            supabase.table("notifications")
            .update(update_data)
            .eq("user_id", str(self.user_id))
            .eq("is_read", False)
            .execute()
        )

        marked_count = len(response.data) if response.data else 0

        return MarkReadResponse(
            marked_count=marked_count,
            message=f"Marked {marked_count} notification(s) as read",
        )

    async def delete_notification(self, notification_id: UUID) -> SuccessMessage:
        """Delete a notification."""
        response = (
            supabase.table("notifications")
            .delete()
            .eq("id", str(notification_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            raise ValueError("Notification not found")

        return SuccessMessage(message="Notification deleted successfully")

    async def create_notification(
        self,
        title: str,
        message: str,
        notification_type: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[UUID] = None,
        send_push: bool = True,
    ) -> NotificationResponse:

        notification_data = {
            "user_id": str(self.user_id),
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "related_entity_type": related_entity_type,
            "related_entity_id": str(related_entity_id) if related_entity_id else None,
            "is_read": False,
        }

        response = supabase.table("notifications").insert(notification_data).execute()

        if not response.data:
            raise Exception("Failed to create notification")

        notification = NotificationResponse(**response.data[0])

        if send_push:
            try:
                from app.services.push_notification_service import PushNotificationService

                push_service = PushNotificationService()
                await push_service.send_push_notification(
                    user_id=self.user_id,
                    title=title,
                    body=message,
                    related_entity_type=related_entity_type,
                    related_entity_id=related_entity_id,
                )
            except Exception as e:
                logger.error(f"Failed to send push notification: {str(e)}")
                logger.info("Notification saved to database despite push failure")

        return notification
