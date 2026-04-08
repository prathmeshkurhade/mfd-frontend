"""Scheduler Service for automated notifications."""

from datetime import date, datetime, time, timedelta
from typing import List, Optional
from uuid import UUID

from app.database import supabase
from app.models.scheduler import (
    DailyScheduleContent,
    EODContent,
    ProgressContent,
    ScheduledNotificationCreate,
    ScheduledNotificationResponse,
)


class SchedulerService:
    """Service for scheduling automated notifications."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def get_daily_schedule_content(self) -> DailyScheduleContent:
        """Get content for morning daily schedule notification."""
        today = date.today()

        # Get today's pending tasks
        tasks_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "pending")
            .execute()
        )
        tasks = tasks_response.data if tasks_response.data else []

        # Get today's touchpoints
        touchpoints_response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", today.isoformat())
            .execute()
        )
        touchpoints = touchpoints_response.data if touchpoints_response.data else []

        # Get today's lead followups
        followups_response = (
            supabase.table("leads")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", today.isoformat())
            .in_("status", ["follow_up", "meeting_scheduled"])
            .execute()
        )
        followups = followups_response.data if followups_response.data else []

        # Get today's birthdays
        all_clients_response = (
            supabase.table("clients")
            .select("id, name, phone, birthdate")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .not_.is_("birthdate", "null")
            .execute()
        )

        birthdays = []
        if all_clients_response.data:
            for client in all_clients_response.data:
                if client.get("birthdate"):
                    try:
                        birthdate = datetime.fromisoformat(
                            client["birthdate"].replace("Z", "+00:00")
                        ).date()
                        if birthdate.month == today.month and birthdate.day == today.day:
                            birthdays.append(client)
                    except Exception:
                        continue

        # Calculate stats
        stats = {
            "total_tasks": len(tasks),
            "total_touchpoints": len(touchpoints),
            "total_followups": len(followups),
            "total_birthdays": len(birthdays),
        }

        return DailyScheduleContent(
            date=today,
            tasks=tasks,
            touchpoints=touchpoints,
            followups=followups,
            birthdays=birthdays,
            stats=stats,
        )

    async def get_progress_content(self) -> ProgressContent:
        """Get content for afternoon progress notification."""
        today = date.today()

        # Get completed tasks today
        completed_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "completed")
            .execute()
        )
        completed_tasks = completed_response.data if completed_response.data else []

        # Get remaining tasks
        remaining_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "pending")
            .execute()
        )
        remaining_tasks = remaining_response.data if remaining_response.data else []

        return ProgressContent(
            completed_count=len(completed_tasks),
            remaining_count=len(remaining_tasks),
            completed_tasks=completed_tasks,
            remaining_tasks=remaining_tasks,
        )

    async def get_eod_content(self) -> EODContent:
        """Get content for end-of-day summary notification."""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Get completed tasks today
        completed_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "completed")
            .execute()
        )
        completed_tasks = completed_response.data if completed_response.data else []

        # Get carried forward tasks
        carry_forward_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "carried_forward")
            .execute()
        )
        carry_forward_tasks = (
            carry_forward_response.data if carry_forward_response.data else []
        )

        # Get tomorrow preview
        tomorrow_tasks_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", tomorrow.isoformat())
            .eq("status", "pending")
            .execute()
        )

        tomorrow_touchpoints_response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", tomorrow.isoformat())
            .execute()
        )

        tomorrow_preview = {
            "tasks": tomorrow_tasks_response.data if tomorrow_tasks_response.data else [],
            "touchpoints": (
                tomorrow_touchpoints_response.data
                if tomorrow_touchpoints_response.data
                else []
            ),
        }

        return EODContent(
            completed_count=len(completed_tasks),
            carry_forward_count=len(carry_forward_tasks),
            completed_tasks=completed_tasks,
            carry_forward_tasks=carry_forward_tasks,
            tomorrow_preview=tomorrow_preview,
        )

    async def create_scheduled_notification(
        self, data: ScheduledNotificationCreate
    ) -> ScheduledNotificationResponse:
        """Create a scheduled notification."""
        notification_data = {
            "user_id": str(self.user_id),
            **data.model_dump(mode="json", exclude_unset=True),
            "status": "pending",
        }

        response = (
            supabase.table("scheduled_notifications").insert(notification_data).execute()
        )

        if not response.data:
            raise Exception("Failed to create scheduled notification")

        return ScheduledNotificationResponse(**response.data[0])

    async def get_pending_notifications(
        self, channel: Optional[str] = None
    ) -> List[ScheduledNotificationResponse]:
        """Get notifications that are ready to be sent."""
        query = (
            supabase.table("scheduled_notifications")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("status", "pending")
            .lte("scheduled_time", datetime.now().isoformat())
        )

        if channel:
            query = query.eq("channel", channel)

        response = query.execute()

        if not response.data:
            return []

        return [ScheduledNotificationResponse(**item) for item in response.data]

    async def mark_notification_sent(
        self, notification_id: UUID, external_message_id: str
    ) -> None:
        """Mark notification as sent."""
        update_data = {
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "external_message_id": external_message_id,
        }

        supabase.table("scheduled_notifications").update(update_data).eq(
            "id", str(notification_id)
        ).eq("user_id", str(self.user_id)).execute()

    async def mark_notification_failed(
        self, notification_id: UUID, error: str
    ) -> None:
        """Mark notification as failed."""
        update_data = {"status": "failed", "error_message": error}

        supabase.table("scheduled_notifications").update(update_data).eq(
            "id", str(notification_id)
        ).eq("user_id", str(self.user_id)).execute()

    async def schedule_daily_notifications_for_user(self) -> None:
        """Schedule all daily notifications for user based on profile preferences."""
        # Get user profile
        profile_response = (
            supabase.table("mfd_profiles")
            .select("*")
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not profile_response.data:
            return

        profile = profile_response.data[0]

        today = date.today()

        # Helper to create notification
        async def schedule_notification(
            notification_type: str,
            channel: str,
            schedule_time: time,
            enabled: bool,
        ):
            if not enabled:
                return

            scheduled_datetime = datetime.combine(today, schedule_time)

            notification_data = ScheduledNotificationCreate(
                notification_type=notification_type,
                channel=channel,
                scheduled_time=scheduled_datetime,
            )

            await self.create_scheduled_notification(notification_data)

        # Morning schedule
        if profile.get("morning_schedule_time"):
            morning_time = datetime.fromisoformat(
                str(profile["morning_schedule_time"])
            ).time()
            
            if profile.get("email_daily_enabled", True):
                await schedule_notification(
                    "morning_schedule", "email", morning_time, True
                )
            if profile.get("whatsapp_daily_enabled", True):
                await schedule_notification(
                    "morning_schedule", "whatsapp", morning_time, True
                )

        # Afternoon progress
        if profile.get("afternoon_schedule_time"):
            afternoon_time = datetime.fromisoformat(
                str(profile["afternoon_schedule_time"])
            ).time()
            
            if profile.get("email_daily_enabled", True):
                await schedule_notification(
                    "afternoon_progress", "email", afternoon_time, True
                )
            if profile.get("whatsapp_daily_enabled", True):
                await schedule_notification(
                    "afternoon_progress", "whatsapp", afternoon_time, True
                )

        # EOD summary
        if profile.get("eod_schedule_time"):
            eod_time = datetime.fromisoformat(str(profile["eod_schedule_time"])).time()
            
            if profile.get("email_daily_enabled", True):
                await schedule_notification("eod_summary", "email", eod_time, True)
            if profile.get("whatsapp_daily_enabled", True):
                await schedule_notification("eod_summary", "whatsapp", eod_time, True)

        # WhatsApp greetings
        if profile.get("whatsapp_greetings_enabled", True):
            await schedule_notification(
                "greeting_gm", "whatsapp", time(7, 0), True
            )
            await schedule_notification(
                "greeting_ge", "whatsapp", time(18, 0), True
            )
            await schedule_notification(
                "greeting_gn", "whatsapp", time(22, 0), True
            )
