"""Webhook Service for processing incoming webhooks from external services."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase_admin
from app.models.webhook import (
    DeliveryStatusPayload,
    WebhookLogResponse,
    WebhookPayload,
    WhatsAppMessagePayload,
)
from app.models.whatsapp_input import ProcessInputResponse


class WebhookService:
    """Service for processing webhooks (system-level, no user_id)."""

    async def log_webhook(self, data: WebhookPayload) -> WebhookLogResponse:
        """Log incoming webhook."""
        webhook_data = {
            "source": data.source,
            "event_type": data.event_type,
            "payload": data.payload,
            "timestamp": (
                data.timestamp.isoformat()
                if data.timestamp
                else datetime.now().isoformat()
            ),
            "processed": False,
        }

        response = (
            supabase_admin.table("webhook_logs").insert(webhook_data).execute()
        )

        if not response.data:
            raise Exception("Failed to log webhook")

        return WebhookLogResponse(**response.data[0])

    async def process_delivery_status(self, payload: DeliveryStatusPayload) -> None:
        """Process delivery status webhook."""
        # Try to find in scheduled_notifications
        scheduled_response = (
            supabase_admin.table("scheduled_notifications")
            .select("*")
            .eq("external_message_id", payload.message_id)
            .execute()
        )

        if scheduled_response.data:
            # Update scheduled notification delivery status
            update_data = {"delivery_status": payload.status}

            if payload.status == "delivered":
                update_data["delivered_at"] = payload.timestamp.isoformat()
            elif payload.status == "read":
                update_data["read_at"] = payload.timestamp.isoformat()
            elif payload.status == "failed":
                update_data["status"] = "failed"
                update_data["error_message"] = payload.error

            supabase_admin.table("scheduled_notifications").update(update_data).eq(
                "id", scheduled_response.data[0]["id"]
            ).execute()

        # Try to find in communication_logs
        comm_response = (
            supabase_admin.table("communication_logs")
            .select("*")
            .eq("external_message_id", payload.message_id)
            .execute()
        )

        if comm_response.data:
            # Update communication log delivery status
            update_data = {"status": payload.status}

            if payload.status == "delivered":
                update_data["delivered_at"] = payload.timestamp.isoformat()
            elif payload.status == "read":
                update_data["read_at"] = payload.timestamp.isoformat()

            supabase_admin.table("communication_logs").update(update_data).eq(
                "id", comm_response.data[0]["id"]
            ).execute()

    async def process_whatsapp_message(
        self, payload: WhatsAppMessagePayload
    ) -> ProcessInputResponse:
        """
        Process incoming WhatsApp message.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - NLP/AI to parse message intent
        - Entity extraction from message
        - Creating appropriate records based on intent
        """
        # Find user by phone number
        user_response = (
            supabase_admin.table("mfd_profiles")
            .select("user_id, phone, whatsapp_number")
            .or_(
                f"phone.eq.{payload.from_number},whatsapp_number.eq.{payload.from_number}"
            )
            .execute()
        )

        if not user_response.data:
            return ProcessInputResponse(
                success=False,
                input_id=UUID("00000000-0000-0000-0000-000000000000"),
                message="User not found for this phone number",
            )

        user_id = user_response.data[0]["user_id"]

        # Create whatsapp_data_inputs record
        input_data = {
            "user_id": user_id,
            "input_type": payload.message_type,
            "raw_message": payload.content,
            "voice_note_url": payload.media_url if payload.message_type == "voice" else None,
            "status": "pending",
        }

        input_response = (
            supabase_admin.table("whatsapp_data_inputs").insert(input_data).execute()
        )

        if not input_response.data:
            return ProcessInputResponse(
                success=False,
                input_id=UUID("00000000-0000-0000-0000-000000000000"),
                message="Failed to create input record",
            )

        input_id = input_response.data[0]["id"]

        # TODO: Implement intent parsing and entity creation
        # This would involve:
        # 1. Parse message to determine intent (add_client, log_touchpoint, etc.)
        # 2. Extract entities from message
        # 3. Create appropriate records in database
        # 4. Update input record with status and created_entity details

        return ProcessInputResponse(
            success=True,
            input_id=UUID(input_id),
            message="Message received and queued for processing",
        )

    async def get_unprocessed_webhooks(
        self, source: Optional[str] = None
    ) -> List[WebhookLogResponse]:
        """Get unprocessed webhooks."""
        query = (
            supabase_admin.table("webhook_logs")
            .select("*")
            .eq("processed", False)
        )

        if source:
            query = query.eq("source", source)

        response = query.order("created_at").execute()

        if not response.data:
            return []

        return [WebhookLogResponse(**item) for item in response.data]

    async def mark_webhook_processed(
        self, webhook_id: UUID, result: Dict[str, Any]
    ) -> None:
        """Mark webhook as processed."""
        update_data = {
            "processed": True,
            "processed_at": datetime.now().isoformat(),
            "processing_result": result,
        }

        supabase_admin.table("webhook_logs").update(update_data).eq(
            "id", str(webhook_id)
        ).execute()
