from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase_admin as supabase
from app.models.lead import LeadCreate, LeadStatusUpdate, LeadUpdate


class LeadService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_leads(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        source: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List leads with filters and pagination."""
        query = (
            supabase.table("leads")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        # Apply search filter
        if search:
            query = query.or_(f"name.ilike.%{search}%,phone.ilike.%{search}%")

        # Apply filters
        if status:
            query = query.eq("status", status)
        if source:
            query = query.eq("source", source)

        # Apply sorting
        order_by = sort_by if sort_by else "created_at"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        leads = response.data if response.data else []
        total = response.count if hasattr(response, "count") else len(leads)

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "leads": leads,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_lead(self, data: LeadCreate) -> Dict[str, Any]:
        """Create a new lead."""
        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)

        # Map API field name to DB column name
        if "referred_by" in insert_data:
            insert_data["sourced_by"] = insert_data.pop("referred_by")

        response = supabase.table("leads").insert(insert_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create lead")

    async def get_lead(self, lead_id: UUID) -> Optional[Dict[str, Any]]:
        """Get lead by ID."""
        response = (
            supabase.table("leads")
            .select("*")
            .eq("id", str(lead_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    async def update_lead(
        self, lead_id: UUID, data: LeadUpdate
    ) -> Dict[str, Any]:
        """Update lead."""
        # Get existing lead
        existing = await self.get_lead(lead_id)
        if not existing:
            raise ValueError("Lead not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Map API field name to DB column name
        if "referred_by" in update_data:
            update_data["sourced_by"] = update_data.pop("referred_by")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("leads")
            .update(update_data)
            .eq("id", str(lead_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        raise Exception("Failed to update lead")

    async def delete_lead(self, lead_id: UUID) -> None:
        """Hard delete lead (leads table has no is_deleted column)."""
        existing = await self.get_lead(lead_id)
        if not existing:
            raise ValueError("Lead not found")

        response = (
            supabase.table("leads")
            .delete()
            .eq("id", str(lead_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Failed to delete lead")

    async def update_status(
        self, lead_id: UUID, data: LeadStatusUpdate
    ) -> Dict[str, Any]:
        """Update lead status."""
        # Get existing lead
        existing = await self.get_lead(lead_id)
        if not existing:
            raise ValueError("Lead not found")

        # Prepare update data
        update_data = {
            "status": data.status.value,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if data.scheduled_date:
            update_data["scheduled_date"] = data.scheduled_date.isoformat()
        if data.scheduled_time:
            update_data["scheduled_time"] = data.scheduled_time
        if data.notes:
            update_data["notes"] = data.notes

        response = (
            supabase.table("leads")
            .update(update_data)
            .eq("id", str(lead_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        raise Exception("Failed to update lead status")

    async def get_today_followups(self) -> List[Dict[str, Any]]:
        """Get leads with scheduled_date = today and status = follow_up or meeting_scheduled."""
        today = date.today().isoformat()
        response = (
            supabase.table("leads")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", today)
            .in_("status", ["follow_up", "meeting_scheduled"])
            .order("scheduled_time", desc=False)
            .execute()
        )
        return response.data if response.data else []
