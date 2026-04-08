"""WhatsApp Input Service for processing MFD data input via WhatsApp."""

import re
from typing import Optional
from uuid import UUID

from app.database import supabase
from app.models.whatsapp_input import (
    ProcessInputResponse,
    WhatsAppDataInputListResponse,
    WhatsAppDataInputResponse,
)


class WhatsAppInputService:
    """Service for processing WhatsApp data inputs."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_inputs(
        self, status: Optional[str] = None
    ) -> WhatsAppDataInputListResponse:
        """List WhatsApp data inputs."""
        query = (
            supabase.table("whatsapp_data_inputs")
            .select("*")
            .eq("user_id", str(self.user_id))
        )

        if status:
            query = query.eq("status", status)

        response = query.order("created_at", desc=True).execute()

        inputs = (
            [WhatsAppDataInputResponse(**inp) for inp in response.data]
            if response.data
            else []
        )

        return WhatsAppDataInputListResponse(inputs=inputs, total=len(inputs))

    async def get_input(self, input_id: UUID) -> Optional[WhatsAppDataInputResponse]:
        """Get WhatsApp input by ID."""
        response = (
            supabase.table("whatsapp_data_inputs")
            .select("*")
            .eq("id", str(input_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            return None

        return WhatsAppDataInputResponse(**response.data[0])

    async def create_input(
        self,
        input_type: str,
        raw_message: Optional[str] = None,
        voice_note_url: Optional[str] = None,
    ) -> WhatsAppDataInputResponse:
        """Create a new WhatsApp input record."""
        input_data = {
            "user_id": str(self.user_id),
            "input_type": input_type,
            "raw_message": raw_message,
            "voice_note_url": voice_note_url,
            "status": "pending",
        }

        response = supabase.table("whatsapp_data_inputs").insert(input_data).execute()

        if not response.data:
            raise Exception("Failed to create WhatsApp input")

        return WhatsAppDataInputResponse(**response.data[0])

    async def process_text_input(
        self, input_id: UUID
    ) -> ProcessInputResponse:
        """
        Process text input and create appropriate entity.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - NLP/AI for better intent recognition
        - More robust entity extraction
        - Validation of extracted data
        """
        # Get input
        input_record = await self.get_input(input_id)
        if not input_record:
            return ProcessInputResponse(
                success=False,
                input_id=input_id,
                message="Input not found",
            )

        if not input_record.raw_message:
            return ProcessInputResponse(
                success=False,
                input_id=input_id,
                message="No message to process",
            )

        try:
            created_entity_type = None
            created_entity_id = None

            # Parse based on input type
            if input_record.input_type == "add_client":
                parsed_data = self.parse_add_client_message(input_record.raw_message)
                if parsed_data:
                    # TODO: Use ClientService to create client
                    # from app.services.client_service import ClientService
                    # client_service = ClientService(self.user_id)
                    # client = await client_service.create_client(ClientCreate(**parsed_data))
                    # created_entity_type = "client"
                    # created_entity_id = client.id
                    created_entity_type = "client"
                    created_entity_id = UUID("00000000-0000-0000-0000-000000000001")

            elif input_record.input_type == "add_lead":
                parsed_data = self.parse_add_lead_message(input_record.raw_message)
                if parsed_data:
                    # TODO: Use LeadService to create lead
                    created_entity_type = "lead"
                    created_entity_id = UUID("00000000-0000-0000-0000-000000000002")

            elif input_record.input_type == "log_touchpoint":
                parsed_data = self.parse_touchpoint_message(input_record.raw_message)
                if parsed_data:
                    # TODO: Use TouchpointService to create touchpoint
                    created_entity_type = "touchpoint"
                    created_entity_id = UUID("00000000-0000-0000-0000-000000000003")

            elif input_record.input_type == "quick_task":
                parsed_data = {"title": input_record.raw_message}
                # TODO: Use TaskService to create task
                created_entity_type = "task"
                created_entity_id = UUID("00000000-0000-0000-0000-000000000004")

            # Update input record
            update_data = {
                "status": "processed",
                "processed_at": "now()",
                "parsed_data": parsed_data if parsed_data else None,
                "created_entity_type": created_entity_type,
                "created_entity_id": str(created_entity_id) if created_entity_id else None,
            }

            supabase.table("whatsapp_data_inputs").update(update_data).eq(
                "id", str(input_id)
            ).execute()

            return ProcessInputResponse(
                success=True,
                input_id=input_id,
                created_entity_type=created_entity_type,
                created_entity_id=created_entity_id,
                message="Input processed successfully",
            )

        except Exception as e:
            # Mark as failed
            supabase.table("whatsapp_data_inputs").update(
                {"status": "failed", "error_message": str(e)}
            ).eq("id", str(input_id)).execute()

            return ProcessInputResponse(
                success=False,
                input_id=input_id,
                message=f"Failed to process input: {str(e)}",
            )

    async def process_voice_input(
        self, input_id: UUID, transcription: str
    ) -> ProcessInputResponse:
        """Process voice input with transcription."""
        # Update input with transcription
        supabase.table("whatsapp_data_inputs").update(
            {"transcription": transcription}
        ).eq("id", str(input_id)).execute()

        # Update raw_message with transcription for parsing
        supabase.table("whatsapp_data_inputs").update(
            {"raw_message": transcription}
        ).eq("id", str(input_id)).execute()

        # Process as text input
        return await self.process_text_input(input_id)

    def parse_add_client_message(self, message: str) -> Optional[dict]:
        """
        Parse add client message.
        
        Expected format: "Add client: Name: John Doe, Phone: +919876543210, Email: john@example.com"
        """
        parsed = {}

        # Extract name
        name_match = re.search(r"[Nn]ame:\s*([^,]+)", message)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        # Extract phone
        phone_match = re.search(r"[Pp]hone:\s*([\+\d]+)", message)
        if phone_match:
            parsed["phone"] = phone_match.group(1).strip()

        # Extract email
        email_match = re.search(r"[Ee]mail:\s*([^\s,]+@[^\s,]+)", message)
        if email_match:
            parsed["email"] = email_match.group(1).strip()

        # Must have at least name and phone
        if "name" in parsed and "phone" in parsed:
            return parsed

        return None

    def parse_add_lead_message(self, message: str) -> Optional[dict]:
        """
        Parse add lead message.
        
        Expected format: "Add lead: Name: Jane Doe, Phone: +919876543210, Source: referral"
        """
        parsed = {}

        # Extract name
        name_match = re.search(r"[Nn]ame:\s*([^,]+)", message)
        if name_match:
            parsed["name"] = name_match.group(1).strip()

        # Extract phone
        phone_match = re.search(r"[Pp]hone:\s*([\+\d]+)", message)
        if phone_match:
            parsed["phone"] = phone_match.group(1).strip()

        # Extract source
        source_match = re.search(r"[Ss]ource:\s*([^,]+)", message)
        if source_match:
            parsed["source"] = source_match.group(1).strip().lower().replace(" ", "_")

        # Must have at least name and phone
        if "name" in parsed and "phone" in parsed:
            parsed["status"] = "follow_up"  # Default status
            return parsed

        return None

    def parse_touchpoint_message(self, message: str) -> Optional[dict]:
        """
        Parse touchpoint message.
        
        Expected format: "Log touchpoint: Client: John Doe, Notes: Discussed portfolio, Outcome: positive"
        """
        parsed = {}

        # Extract client name/phone
        client_match = re.search(r"[Cc]lient:\s*([^,]+)", message)
        if client_match:
            parsed["client_identifier"] = client_match.group(1).strip()

        # Extract notes
        notes_match = re.search(r"[Nn]otes:\s*([^,]+)", message)
        if notes_match:
            parsed["notes"] = notes_match.group(1).strip()

        # Extract outcome
        outcome_match = re.search(r"[Oo]utcome:\s*([^,]+)", message)
        if outcome_match:
            parsed["outcome"] = outcome_match.group(1).strip()

        # Must have at least client identifier
        if "client_identifier" in parsed:
            return parsed

        return None
