"""Campaign Service for marketing campaigns."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase
from app.models.campaign import (
    CampaignCreate,
    CampaignExecuteResponse,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdate,
)
from app.models.common import SuccessMessage


class CampaignService:
    """Service for managing campaigns."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_campaigns(
        self, page: int = 1, limit: int = 20
    ) -> CampaignListResponse:
        """List campaigns with pagination."""
        offset = (page - 1) * limit

        response = (
            supabase.table("campaigns")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        campaigns = (
            [CampaignResponse(**camp) for camp in response.data]
            if response.data
            else []
        )

        total = response.count if response.count is not None else 0
        total_pages = (total + limit - 1) // limit

        return CampaignListResponse(
            campaigns=campaigns,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    async def create_campaign(self, data: CampaignCreate) -> CampaignResponse:
        """Create a new campaign."""
        # Calculate total recipients
        total_recipients = len(data.client_ids) if data.client_ids else 0

        # If filters are provided, count matching clients
        if data.filters and not data.client_ids:
            # TODO: Implement dynamic filtering based on filters dict
            # For now, just set to 0
            total_recipients = 0

        campaign_data = {
            "user_id": str(self.user_id),
            **data.model_dump(mode="json", exclude_unset=True, exclude={"client_ids"}),
            "total_recipients": total_recipients,
        }

        response = supabase.table("campaigns").insert(campaign_data).execute()

        if not response.data:
            raise Exception("Failed to create campaign")

        campaign_id = response.data[0]["id"]

        # Insert campaign_clients relationships
        if data.client_ids:
            client_links = [
                {
                    "campaign_id": campaign_id,
                    "client_id": str(client_id),
                    "send_status": "pending",
                }
                for client_id in data.client_ids
            ]

            supabase.table("campaign_clients").insert(client_links).execute()

        return CampaignResponse(**response.data[0])

    async def get_campaign(self, campaign_id: UUID) -> Optional[CampaignResponse]:
        """Get campaign by ID."""
        response = (
            supabase.table("campaigns")
            .select("*")
            .eq("id", str(campaign_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            return None

        return CampaignResponse(**response.data[0])

    async def update_campaign(
        self, campaign_id: UUID, data: CampaignUpdate
    ) -> CampaignResponse:
        """Update campaign (only if not executed)."""
        # Check if campaign exists and is not executed
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.is_executed:
            raise ValueError("Cannot update executed campaign")

        update_data = data.model_dump(mode="json", exclude_unset=True, exclude={"client_ids"})

        if not update_data and not data.client_ids:
            raise ValueError("No fields to update")

        # Update campaign
        if update_data:
            response = (
                supabase.table("campaigns")
                .update(update_data)
                .eq("id", str(campaign_id))
                .eq("user_id", str(self.user_id))
                .execute()
            )

            if not response.data:
                raise ValueError("Campaign not found")

        # Update client_ids if provided
        if data.client_ids is not None:
            # Delete existing links
            supabase.table("campaign_clients").delete().eq(
                "campaign_id", str(campaign_id)
            ).execute()

            # Insert new links
            if data.client_ids:
                client_links = [
                    {
                        "campaign_id": str(campaign_id),
                        "client_id": str(client_id),
                        "send_status": "pending",
                    }
                    for client_id in data.client_ids
                ]
                supabase.table("campaign_clients").insert(client_links).execute()

            # Update total_recipients
            supabase.table("campaigns").update(
                {"total_recipients": len(data.client_ids)}
            ).eq("id", str(campaign_id)).execute()

        # Get updated campaign
        updated = await self.get_campaign(campaign_id)
        if not updated:
            raise ValueError("Failed to retrieve updated campaign")

        return updated

    async def delete_campaign(self, campaign_id: UUID) -> SuccessMessage:
        """Delete campaign (only if not executed)."""
        # Check if campaign exists and is not executed
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.is_executed:
            raise ValueError("Cannot delete executed campaign")

        # Delete campaign_clients links first (foreign key constraint)
        supabase.table("campaign_clients").delete().eq(
            "campaign_id", str(campaign_id)
        ).execute()

        # Delete campaign
        supabase.table("campaigns").delete().eq("id", str(campaign_id)).eq(
            "user_id", str(self.user_id)
        ).execute()

        return SuccessMessage(message="Campaign deleted successfully")

    async def preview_campaign(self, campaign_id: UUID) -> Dict[str, Any]:
        """Preview campaign with sample recipients and message."""
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        # Get sample recipients (first 5)
        recipients_response = (
            supabase.table("campaign_clients")
            .select("client_id")
            .eq("campaign_id", str(campaign_id))
            .limit(5)
            .execute()
        )

        recipient_ids = (
            [r["client_id"] for r in recipients_response.data]
            if recipients_response.data
            else []
        )

        # Get client details for preview
        sample_recipients = []
        if recipient_ids:
            clients_response = (
                supabase.table("clients")
                .select("id, name, phone, email")
                .in_("id", recipient_ids)
                .execute()
            )

            sample_recipients = clients_response.data if clients_response.data else []

        # Generate sample message (replace placeholders if any)
        sample_message = campaign.message_template or "No message template"

        # Simple placeholder replacement for preview
        if sample_recipients:
            first_client = sample_recipients[0]
            sample_message = sample_message.replace("{name}", first_client.get("name", "Client"))
            sample_message = sample_message.replace("{client_name}", first_client.get("name", "Client"))

        return {
            "campaign_id": str(campaign_id),
            "campaign_name": campaign.name,
            "total_recipients": campaign.total_recipients,
            "sample_recipients": sample_recipients,
            "sample_message": sample_message,
            "channel": campaign.channel,
        }

    async def execute_campaign(self, campaign_id: UUID) -> CampaignExecuteResponse:
        """
        Execute campaign and send to all recipients.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - WhatsApp Business API integration
        - Email service integration
        - Queue system for bulk sending
        - Rate limiting and retry logic
        """
        # Get campaign
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")

        if campaign.is_executed:
            raise ValueError("Campaign already executed")

        # Get all recipients
        recipients_response = (
            supabase.table("campaign_clients")
            .select("client_id")
            .eq("campaign_id", str(campaign_id))
            .execute()
        )

        recipient_ids = (
            [r["client_id"] for r in recipients_response.data]
            if recipients_response.data
            else []
        )

        # Get client details
        clients = []
        if recipient_ids:
            clients_response = (
                supabase.table("clients")
                .select("id, name, phone, email")
                .in_("id", recipient_ids)
                .execute()
            )
            clients = clients_response.data if clients_response.data else []

        # Track sending results
        successful_sends = 0
        failed_sends = 0

        # STUB: Simulate sending to each recipient
        for client in clients:
            try:
                # TODO: Actual sending logic
                # if campaign.channel == "whatsapp":
                #     # Send via WhatsApp Business API
                #     send_whatsapp(client["phone"], campaign.message_template)
                # elif campaign.channel == "email":
                #     # Send via email service
                #     send_email(client["email"], campaign.name, campaign.message_template)

                # Update campaign_clients status
                supabase.table("campaign_clients").update(
                    {"send_status": "sent", "sent_at": datetime.now().isoformat()}
                ).eq("campaign_id", str(campaign_id)).eq(
                    "client_id", client["id"]
                ).execute()

                successful_sends += 1
            except Exception:
                # Mark as failed
                supabase.table("campaign_clients").update(
                    {"send_status": "failed"}
                ).eq("campaign_id", str(campaign_id)).eq(
                    "client_id", client["id"]
                ).execute()

                failed_sends += 1

        # Update campaign as executed
        update_data = {
            "is_executed": True,
            "executed_at": datetime.now().isoformat(),
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
        }

        supabase.table("campaigns").update(update_data).eq(
            "id", str(campaign_id)
        ).execute()

        return CampaignExecuteResponse(
            campaign_id=campaign_id,
            total_recipients=len(clients),
            successful=successful_sends,
            failed=failed_sends,
            message=f"Campaign executed: {successful_sends} successful, {failed_sends} failed",
        )

    async def get_birthday_clients_today(self) -> List[Dict[str, Any]]:
        """Get clients with birthdays today for auto birthday campaign."""
        today = date.today()
        month = today.month
        day = today.day

        # Query clients where birthdate month and day match today
        # NOTE: This requires PostgreSQL date functions
        # Using EXTRACT or date_part to compare month and day
        
        # Get all clients and filter in Python (simpler for now)
        response = (
            supabase.table("clients")
            .select("id, name, phone, email, birthdate")
            .eq("user_id", str(self.user_id))
            .not_.is_("birthdate", "null")
            .execute()
        )

        if not response.data:
            return []

        # Filter clients with birthday today
        birthday_clients = []
        for client in response.data:
            if client.get("birthdate"):
                try:
                    birthdate = datetime.fromisoformat(
                        client["birthdate"].replace("Z", "+00:00")
                    ).date()
                    if birthdate.month == month and birthdate.day == day:
                        birthday_clients.append(client)
                except Exception:
                    continue

        return birthday_clients
