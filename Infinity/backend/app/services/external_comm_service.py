"""External Communication Service for sending messages via WhatsApp and Email."""

from typing import Optional

import httpx

from app.config import settings
from app.models.profile import ProfileResponse
from app.models.scheduler import ScheduledNotificationResponse
from app.services.template_service import TemplateService


class ExternalCommService:
    """Service for sending messages to external WhatsApp and Email services."""

    def __init__(self):
        """Initialize HTTP client and load endpoints from settings."""
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Load endpoints from settings
        self.whatsapp_notif_endpoint = getattr(
            settings, "WHATSAPP_NOTIF_ENDPOINT", ""
        )
        self.whatsapp_input_endpoint = getattr(
            settings, "WHATSAPP_INPUT_ENDPOINT", ""
        )
        self.email_service_endpoint = getattr(
            settings, "EMAIL_SERVICE_ENDPOINT", ""
        )

    async def send_to_whatsapp_notif(
        self, phone: str, message: str, template_id: Optional[str] = None
    ) -> dict:
        """
        Send message via WhatsApp Business Account #1 (Notifications).
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - WhatsApp Business API integration
        - Template approval and management
        - Message queueing and rate limiting
        """
        if not self.whatsapp_notif_endpoint:
            return {
                "success": False,
                "message_id": None,
                "error": "WhatsApp notification endpoint not configured",
            }

        try:
            payload = {"phone": phone, "message": message}

            if template_id:
                payload["template_id"] = template_id

            # STUB: Actual API call would go here
            # response = await self.client.post(
            #     self.whatsapp_notif_endpoint,
            #     json=payload
            # )
            # response.raise_for_status()
            # return response.json()

            # Simulated response
            return {
                "success": True,
                "message_id": "wa_notif_" + phone[-10:],
                "error": None,
            }

        except httpx.HTTPError as e:
            return {"success": False, "message_id": None, "error": str(e)}

    async def send_email(self, to_email: str, subject: str, body_html: str) -> dict:
        """
        Send email via Email Service.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - Email service provider (SendGrid, SES, etc.)
        - HTML email templates
        - Bounce and complaint handling
        """
        if not self.email_service_endpoint:
            return {
                "success": False,
                "message_id": None,
                "error": "Email service endpoint not configured",
            }

        try:
            payload = {"to_email": to_email, "subject": subject, "body_html": body_html}

            # STUB: Actual API call would go here
            # response = await self.client.post(
            #     self.email_service_endpoint,
            #     json=payload
            # )
            # response.raise_for_status()
            # return response.json()

            # Simulated response
            return {
                "success": True,
                "message_id": "email_" + to_email.split("@")[0],
                "error": None,
            }

        except httpx.HTTPError as e:
            return {"success": False, "message_id": None, "error": str(e)}

    async def send_scheduled_notification(
        self, notification: ScheduledNotificationResponse, profile: ProfileResponse
    ) -> dict:
        """Send a scheduled notification based on its type and channel."""
        # Get template service
        template_service = TemplateService(notification.user_id)

        # Get appropriate template
        template = await template_service.get_template_by_type(
            notification.notification_type, notification.channel
        )

        if not template:
            return {
                "success": False,
                "message_id": None,
                "error": f"No template found for {notification.notification_type} on {notification.channel}",
            }

        # Prepare template variables
        variables = {
            "mfd_name": profile.name,
            "notification_type": notification.notification_type,
        }

        # Add notification content if available
        if notification.content:
            variables.update(notification.content)

        # Render template
        rendered = template_service.render_template(template, variables)

        # Send based on channel
        if notification.channel == "whatsapp":
            phone = profile.whatsapp_number or profile.phone
            return await self.send_to_whatsapp_notif(
                phone=phone,
                message=rendered["rendered_content"],
                template_id=str(template.id),
            )

        elif notification.channel == "email":
            # Determine email from profile
            # Note: Profile model doesn't have email field in current schema
            # You might need to get it from user's auth record or add to profile
            email = getattr(profile, "email", None) or f"user_{profile.user_id}@example.com"
            
            return await self.send_email(
                to_email=email,
                subject=rendered["rendered_subject"] or notification.notification_type,
                body_html=rendered["rendered_content"],
            )

        else:
            return {
                "success": False,
                "message_id": None,
                "error": f"Unsupported channel: {notification.channel}",
            }

    async def respond_to_whatsapp_input(self, phone: str, message: str) -> dict:
        """
        Send response back to MFD via WhatsApp Business Account #2 (Input).
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - WhatsApp Business API integration for inbound messages
        - Two-way conversation handling
        - Session management
        """
        if not self.whatsapp_input_endpoint:
            return {
                "success": False,
                "message_id": None,
                "error": "WhatsApp input endpoint not configured",
            }

        try:
            payload = {"phone": phone, "message": message}

            # STUB: Actual API call would go here
            # response = await self.client.post(
            #     f"{self.whatsapp_input_endpoint}/respond",
            #     json=payload
            # )
            # response.raise_for_status()
            # return response.json()

            # Simulated response
            return {
                "success": True,
                "message_id": "wa_input_" + phone[-10:],
                "error": None,
            }

        except httpx.HTTPError as e:
            return {"success": False, "message_id": None, "error": str(e)}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
