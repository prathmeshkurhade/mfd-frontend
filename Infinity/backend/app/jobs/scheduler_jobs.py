"""Background scheduler jobs for automated tasks."""

import logging
from datetime import date, datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.database import supabase, supabase_admin
from app.services.external_comm_service import ExternalCommService
from app.services.notification_service import NotificationService
from app.services.profile_service import ProfileService
from app.services.scheduler_service import SchedulerService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def schedule_all_daily_notifications():
    """
    Run at midnight (00:05) - Schedule today's notifications for all users.
    Creates scheduled_notifications for the day based on user preferences.
    """
    logger.info("Starting daily notification scheduling job...")

    try:
        # Get all active MFD profiles
        response = (
            supabase.table("mfd_profiles")
            .select("user_id, morning_schedule_time, afternoon_schedule_time, eod_schedule_time, "
                    "email_daily_enabled, whatsapp_daily_enabled, whatsapp_greetings_enabled")
            .execute()
        )

        if not response.data:
            logger.info("No MFD profiles found")
            return

        profiles = response.data
        logger.info(f"Found {len(profiles)} profiles to schedule notifications for")

        for profile in profiles:
            user_id = profile["user_id"]

            try:
                # Initialize scheduler service for this user
                scheduler_service = SchedulerService(user_id)

                # Schedule daily notifications for this user
                # This will create records in scheduled_notifications table
                # based on their preference times
                scheduler_service.schedule_daily_notifications_for_user()

                logger.info(f"Scheduled notifications for user {user_id}")

            except Exception as e:
                logger.error(f"Error scheduling notifications for user {user_id}: {str(e)}")
                continue

        logger.info("Daily notification scheduling job completed")

    except Exception as e:
        logger.error(f"Error in schedule_all_daily_notifications: {str(e)}")


def process_pending_notifications():
    """
    Run every minute - Send pending notifications that are due.
    Processes scheduled_notifications where status=pending and scheduled_time <= now.
    """
    try:
        # Get all pending notifications that are due
        current_time = datetime.now().isoformat()

        response = (
            supabase.table("scheduled_notifications")
            .select("id, user_id, notification_type, channel, scheduled_time")
            .eq("status", "pending")
            .lte("scheduled_time", current_time)
            .limit(50)  # Process max 50 at a time
            .execute()
        )

        if not response.data:
            return  # No pending notifications

        notifications = response.data
        logger.info(f"Processing {len(notifications)} pending notifications")

        # Initialize external comm service
        comm_service = ExternalCommService()

        for notif in notifications:
            try:
                user_id = notif["user_id"]

                # Get user profile
                profile_service = ProfileService(user_id)
                profile = profile_service.get_profile()

                if not profile:
                    logger.warning(f"Profile not found for user {user_id}, skipping notification {notif['id']}")
                    continue

                # Get scheduler service to fetch full notification
                scheduler_service = SchedulerService(user_id)

                # Send notification via external service
                result = comm_service.send_scheduled_notification(notif, profile)

                # Update notification status
                if result.get("success"):
                    scheduler_service.mark_notification_sent(
                        notif["id"],
                        result.get("message_id", "")
                    )
                else:
                    scheduler_service.mark_notification_failed(
                        notif["id"],
                        result.get("error", "Unknown error")
                    )

            except Exception as e:
                logger.error(f"Error processing notification {notif['id']}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in process_pending_notifications: {str(e)}")


def process_webhook_queue():
    """
    Run every minute - Process unprocessed webhooks.
    Processes webhook_logs where processed=False.
    """
    try:
        # Get unprocessed webhooks
        response = (
            supabase_admin.table("webhook_logs")
            .select("*")
            .eq("processed", False)
            .limit(50)  # Process max 50 at a time
            .execute()
        )

        if not response.data:
            return  # No unprocessed webhooks

        webhooks = response.data
        logger.info(f"Processing {len(webhooks)} unprocessed webhooks")

        for webhook in webhooks:
            try:
                webhook_id = webhook["id"]
                event_type = webhook.get("event_type", "")

                # Process based on event type
                if event_type in ["delivery_status", "whatsapp_delivery"]:
                    # Process delivery status updates
                    # This would update scheduled_notifications or communication_logs
                    pass

                elif event_type in ["whatsapp_message", "incoming_message"]:
                    # Process incoming WhatsApp messages
                    # This would create whatsapp_data_inputs records
                    pass

                # Mark as processed
                supabase_admin.table("webhook_logs").update(
                    {
                        "processed": True,
                        "processed_at": datetime.now().isoformat(),
                        "processing_result": {"status": "success"}
                    }
                ).eq("id", webhook_id).execute()

                logger.info(f"Processed webhook {webhook_id}")

            except Exception as e:
                logger.error(f"Error processing webhook {webhook['id']}: {str(e)}")
                
                # Mark as processed with error
                supabase_admin.table("webhook_logs").update(
                    {
                        "processed": True,
                        "processed_at": datetime.now().isoformat(),
                        "processing_result": {"status": "error", "error": str(e)}
                    }
                ).eq("id", webhook["id"]).execute()
                continue

    except Exception as e:
        logger.error(f"Error in process_webhook_queue: {str(e)}")


def check_birthdays_and_notify():
    """
    Run at 8am - Notify MFDs about client birthdays today.
    Creates notifications for MFDs about their clients' birthdays.
    """
    logger.info("Starting birthday notification job...")

    try:
        today = date.today()
        today_month = today.month
        today_day = today.day

        # Get all clients with birthday today (regardless of user)
        # Note: This is a simplified query. In production, you'd use proper date filtering
        response = (
            supabase.table("clients")
            .select("id, user_id, name, phone, birthdate")
            .eq("is_deleted", False)
            .execute()
        )

        if not response.data:
            logger.info("No clients found")
            return

        clients = response.data
        birthday_clients_by_user = {}

        # Filter clients with birthday today
        for client in clients:
            if client.get("birthdate"):
                try:
                    birthdate = datetime.fromisoformat(client["birthdate"]).date()
                    if birthdate.month == today_month and birthdate.day == today_day:
                        user_id = client["user_id"]
                        if user_id not in birthday_clients_by_user:
                            birthday_clients_by_user[user_id] = []
                        birthday_clients_by_user[user_id].append(client)
                except Exception:
                    continue

        if not birthday_clients_by_user:
            logger.info("No birthdays today")
            return

        logger.info(f"Found birthdays for {len(birthday_clients_by_user)} users")

        # Create notifications for each MFD
        for user_id, clients_list in birthday_clients_by_user.items():
            try:
                notification_service = NotificationService(user_id)

                client_names = ", ".join([c["name"] for c in clients_list])
                count = len(clients_list)

                title = f"{count} Birthday{'s' if count > 1 else ''} Today!"
                message = f"Today is the birthday of: {client_names}. Don't forget to wish them!"

                notification_service.create_notification(
                    title=title,
                    message=message,
                    notification_type="birthday_reminder",
                    related_entity_type="client",
                    related_entity_id=clients_list[0]["id"] if count == 1 else None
                )

                logger.info(f"Created birthday notification for user {user_id}")

            except Exception as e:
                logger.error(f"Error creating birthday notification for user {user_id}: {str(e)}")
                continue

        logger.info("Birthday notification job completed")

    except Exception as e:
        logger.error(f"Error in check_birthdays_and_notify: {str(e)}")


def auto_carry_forward_tasks():
    """
    Run at midnight (00:01) - Auto carry forward overdue tasks.
    Updates tasks where due_date < today and status = pending.
    """
    logger.info("Starting auto carry forward tasks job...")

    try:
        today = date.today().isoformat()

        # Get all overdue pending tasks
        response = (
            supabase.table("tasks")
            .select("id, user_id, title")
            .eq("status", "pending")
            .lt("due_date", today)
            .limit(1000)  # Process max 1000 at a time
            .execute()
        )

        if not response.data:
            logger.info("No overdue tasks to carry forward")
            return

        tasks = response.data
        logger.info(f"Found {len(tasks)} overdue tasks to carry forward")

        for task in tasks:
            try:
                task_id = task["id"]

                # Get current carry_forward_count
                task_detail = (
                    supabase.table("tasks")
                    .select("carry_forward_count")
                    .eq("id", task_id)
                    .execute()
                )

                current_count = task_detail.data[0].get("carry_forward_count", 0) if task_detail.data else 0

                # Update task status and increment count
                supabase.table("tasks").update(
                    {
                        "status": "carried_forward",
                        "carry_forward_count": current_count + 1
                    }
                ).eq("id", task_id).execute()

                logger.info(f"Carried forward task {task_id}")

            except Exception as e:
                logger.error(f"Error carrying forward task {task['id']}: {str(e)}")
                continue

        logger.info(f"Auto carry forward completed: {len(tasks)} tasks updated")

    except Exception as e:
        logger.error(f"Error in auto_carry_forward_tasks: {str(e)}")


def start_scheduler():
    """Start the background scheduler with all jobs."""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    logger.info("Starting background scheduler...")

    scheduler = BackgroundScheduler()

    # Add jobs with their schedules
    scheduler.add_job(
        schedule_all_daily_notifications,
        "cron",
        hour=0,
        minute=5,
        id="schedule_daily_notifications",
    )

    scheduler.add_job(
        process_pending_notifications,
        "interval",
        minutes=1,
        id="process_pending_notifications",
    )

    scheduler.add_job(
        process_webhook_queue,
        "interval",
        minutes=1,
        id="process_webhook_queue",
    )

    scheduler.add_job(
        check_birthdays_and_notify,
        "cron",
        hour=8,
        minute=0,
        id="check_birthdays_and_notify",
    )

    scheduler.add_job(
        auto_carry_forward_tasks,
        "cron",
        hour=0,
        minute=1,
        id="auto_carry_forward_tasks",
    )

    scheduler.start()
    logger.info("Background scheduler started successfully")


def shutdown_scheduler():
    """Shutdown the background scheduler."""
    global scheduler

    if scheduler is not None:
        logger.info("Shutting down background scheduler...")
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
