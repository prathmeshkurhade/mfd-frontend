from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase
from app.models.touchpoint import (
    ClientTouchpointStats,
    MOMUpdate,
    MOMResponse,
    TouchpointComplete,
    TouchpointCreate,
    TouchpointResponse,
    TouchpointUpdate,
)


class TouchpointService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_touchpoints(
        self,
        page: int = 1,
        limit: int = 20,
        client_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        status: Optional[str] = None,
        interaction_type: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        sort_by: str = "scheduled_date",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List touchpoints with filters and pagination."""
        query = (
            supabase.table("touchpoints")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters
        if client_id:
            query = query.eq("client_id", str(client_id))
        if lead_id:
            query = query.eq("lead_id", str(lead_id))
        if status:
            query = query.eq("status", status)
        if interaction_type:
            query = query.eq("interaction_type", interaction_type)
        if date_from:
            query = query.gte("scheduled_date", date_from.isoformat())
        if date_to:
            query = query.lte("scheduled_date", date_to.isoformat())

        # Apply sorting
        order_by = sort_by if sort_by else "scheduled_date"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        touchpoints = response.data if response.data else []
        total = response.count if hasattr(response, "count") else len(touchpoints)

        # Enrich with client/lead names
        enriched_touchpoints = []
        for tp in touchpoints:
            enriched = tp.copy()
            if tp.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", tp["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            if tp.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", tp["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    enriched["lead_name"] = lead_resp.data.get("name")
            # Map purpose to agenda for response
            if "purpose" in enriched:
                enriched["agenda"] = enriched.pop("purpose")
            enriched_touchpoints.append(enriched)

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "touchpoints": enriched_touchpoints,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_touchpoint(self, data: TouchpointCreate) -> Dict[str, Any]:
        """Create a new touchpoint."""
        # Validate that either client_id or lead_id is provided
        if not data.client_id and not data.lead_id:
            raise ValueError("Either client_id or lead_id must be provided")

        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)

        # Map agenda to purpose (database uses purpose)
        if "agenda" in insert_data:
            insert_data["purpose"] = insert_data.pop("agenda")

        response = supabase.table("touchpoints").insert(insert_data).execute()
        if response.data:
            touchpoint = response.data[0]
            # Map purpose back to agenda for response
            if "purpose" in touchpoint:
                touchpoint["agenda"] = touchpoint.pop("purpose")
            return touchpoint
        raise Exception("Failed to create touchpoint")

    async def get_touchpoint(self, touchpoint_id: UUID) -> Optional[Dict[str, Any]]:
        """Get touchpoint by ID."""
        response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            touchpoint = response.data[0]
            # Enrich with client/lead names
            if touchpoint.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", touchpoint["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    touchpoint["client_name"] = client_resp.data.get("name")
            if touchpoint.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", touchpoint["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    touchpoint["lead_name"] = lead_resp.data.get("name")
            # Map purpose to agenda
            if "purpose" in touchpoint:
                touchpoint["agenda"] = touchpoint.pop("purpose")
            return touchpoint
        return None

    async def update_touchpoint(
        self, touchpoint_id: UUID, data: TouchpointUpdate
    ) -> Dict[str, Any]:
        """Update touchpoint."""
        # Get existing touchpoint
        existing = await self.get_touchpoint(touchpoint_id)
        if not existing:
            raise ValueError("Touchpoint not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Map agenda to purpose
        if "agenda" in update_data:
            update_data["purpose"] = update_data.pop("agenda")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("touchpoints")
            .update(update_data)
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            touchpoint = response.data[0]
            # Map purpose back to agenda
            if "purpose" in touchpoint:
                touchpoint["agenda"] = touchpoint.pop("purpose")
            return touchpoint
        raise Exception("Failed to update touchpoint")

    async def delete_touchpoint(self, touchpoint_id: UUID) -> None:
        """Soft delete touchpoint."""
        # Check if touchpoint exists
        existing = await self.get_touchpoint(touchpoint_id)
        if not existing:
            raise ValueError("Touchpoint not found")

        # Note: Schema doesn't show is_deleted for touchpoints
        # Using hard delete for now, but can be changed to soft delete if column is added
        response = (
            supabase.table("touchpoints")
            .delete()
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Failed to delete touchpoint")

    async def complete_touchpoint(
        self, touchpoint_id: UUID, data: TouchpointComplete
    ) -> Dict[str, Any]:
        """Complete touchpoint and optionally create task/BO."""
        # Get existing touchpoint
        existing = await self.get_touchpoint(touchpoint_id)
        if not existing:
            raise ValueError("Touchpoint not found")

        # Prepare update data
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store completion details in mom_text if available
        completion_notes = []
        if data.actual_date:
            completion_notes.append(f"Actual Date: {data.actual_date.isoformat()}")
        if data.actual_time:
            completion_notes.append(f"Actual Time: {data.actual_time}")
        if data.duration_minutes:
            completion_notes.append(f"Duration: {data.duration_minutes} minutes")
        if data.notes:
            completion_notes.append(f"Notes: {data.notes}")

        # Update mom_text
        if data.mom_text:
            update_data["mom_text"] = data.mom_text
        elif completion_notes:
            update_data["mom_text"] = "\n".join(completion_notes)

        # Store outcome if provided (note: schema doesn't have outcome column, storing in mom_text)
        if data.outcome:
            outcome_text = f"\nOutcome: {data.outcome.value}"
            if "mom_text" in update_data:
                update_data["mom_text"] += outcome_text
            else:
                update_data["mom_text"] = outcome_text

        # Update touchpoint
        response = (
            supabase.table("touchpoints")
            .update(update_data)
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise Exception("Failed to complete touchpoint")

        touchpoint = response.data[0]

        # Create follow-up task if requested
        if data.create_follow_up_task and data.follow_up_task_title:
            task_data = {
                "user_id": str(self.user_id),
                "description": data.follow_up_task_title,
                "due_date": (
                    data.follow_up_task_date.isoformat()
                    if data.follow_up_task_date
                    else date.today().isoformat()
                ),
                "status": "pending",
                "priority": "medium",
            }
            if existing.get("client_id"):
                task_data["client_id"] = existing["client_id"]
            if existing.get("lead_id"):
                task_data["lead_id"] = existing["lead_id"]

            supabase.table("tasks").insert(task_data).execute()

        # Create business opportunity if requested
        if data.create_business_opportunity and data.opportunity_type:
            bo_data = {
                "user_id": str(self.user_id),
                "opportunity_type": data.opportunity_type.value,
                "opportunity_stage": "identified",
                "opportunity_source": "client_servicing",
                "expected_amount": data.opportunity_amount or 0,
                "due_date": date.today().isoformat(),
            }
            if existing.get("client_id"):
                bo_data["client_id"] = existing["client_id"]
            if existing.get("lead_id"):
                bo_data["lead_id"] = existing["lead_id"]
            if data.notes:
                bo_data["additional_info"] = data.notes

            supabase.table("business_opportunities").insert(bo_data).execute()

        # Map purpose to agenda for response
        if "purpose" in touchpoint:
            touchpoint["agenda"] = touchpoint.pop("purpose")
        return touchpoint

    async def update_mom(
        self, touchpoint_id: UUID, data: MOMUpdate
    ) -> MOMResponse:
        """Update MoM text."""
        # Get existing touchpoint
        existing = await self.get_touchpoint(touchpoint_id)
        if not existing:
            raise ValueError("Touchpoint not found")

        update_data = {
            "mom_text": data.mom_text,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = (
            supabase.table("touchpoints")
            .update(update_data)
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise Exception("Failed to update MoM")

        touchpoint = response.data[0]
        return MOMResponse(
            touchpoint_id=touchpoint_id,
            mom_text=touchpoint.get("mom_text"),
            mom_pdf_url=touchpoint.get("mom_pdf_url"),
        )

    async def reschedule(
        self, touchpoint_id: UUID, new_date: date, new_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reschedule touchpoint."""
        # Get existing touchpoint
        existing = await self.get_touchpoint(touchpoint_id)
        if not existing:
            raise ValueError("Touchpoint not found")

        update_data = {
            "status": "rescheduled",
            "scheduled_date": new_date.isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if new_time:
            update_data["scheduled_time"] = new_time

        response = (
            supabase.table("touchpoints")
            .update(update_data)
            .eq("id", str(touchpoint_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            touchpoint = response.data[0]
            # Map purpose to agenda
            if "purpose" in touchpoint:
                touchpoint["agenda"] = touchpoint.pop("purpose")
            return touchpoint
        raise Exception("Failed to reschedule touchpoint")

    async def get_client_touchpoints(
        self, client_id: UUID
    ) -> ClientTouchpointStats:
        """Get all touchpoints for a client with stats."""
        response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("client_id", str(client_id))
            .order("scheduled_date", desc=True)
            .execute()
        )

        touchpoints = response.data if response.data else []
        current_year = date.today().year

        # Calculate stats
        total_touchpoints = len(touchpoints)
        completed_touchpoints = sum(
            1 for tp in touchpoints if tp.get("status") == "completed"
        )
        this_year_count = sum(
            1
            for tp in touchpoints
            if tp.get("scheduled_date")
            and datetime.fromisoformat(tp["scheduled_date"]).year == current_year
        )

        last_touchpoint_date = None
        if touchpoints:
            last_date_str = touchpoints[0].get("scheduled_date")
            if last_date_str:
                last_touchpoint_date = datetime.fromisoformat(
                    last_date_str
                ).date()

        # Enrich touchpoints and convert to TouchpointResponse format
        enriched_touchpoints = []
        for tp in touchpoints:
            enriched = tp.copy()
            # Map purpose to agenda
            if "purpose" in enriched:
                enriched["agenda"] = enriched.pop("purpose")
            # Convert to TouchpointResponse
            # Pydantic will handle type conversions automatically
            enriched_touchpoints.append(TouchpointResponse(**enriched))

        return ClientTouchpointStats(
            client_id=client_id,
            total_touchpoints=total_touchpoints,
            completed_touchpoints=completed_touchpoints,
            this_year_count=this_year_count,
            last_touchpoint_date=last_touchpoint_date,
            touchpoints=enriched_touchpoints,
        )

    async def get_upcoming(self) -> List[Dict[str, Any]]:
        """Get upcoming touchpoints."""
        today = date.today().isoformat()
        response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("status", "scheduled")
            .gte("scheduled_date", today)
            .order("scheduled_date", desc=False)
            .order("scheduled_time", desc=False)
            .execute()
        )

        touchpoints = response.data if response.data else []

        # Enrich with client/lead names
        enriched_touchpoints = []
        for tp in touchpoints:
            enriched = tp.copy()
            if tp.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", tp["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            if tp.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", tp["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    enriched["lead_name"] = lead_resp.data.get("name")
            # Map purpose to agenda
            if "purpose" in enriched:
                enriched["agenda"] = enriched.pop("purpose")
            enriched_touchpoints.append(enriched)

        return enriched_touchpoints
