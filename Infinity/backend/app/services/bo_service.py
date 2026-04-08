from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase
from app.models.business_opportunity import (
    BOCreate,
    BOListResponse,
    BOOutcomeUpdate,
    BOPipelineResponse,
    BOPipelineStage,
    BOResponse,
    BOUpdate,
)


class BOService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_opportunities(
        self,
        page: int = 1,
        limit: int = 20,
        client_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        opportunity_type: Optional[str] = None,
        stage: Optional[str] = None,
        outcome: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List business opportunities with filters and pagination."""
        query = (
            supabase.table("business_opportunities")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters
        if client_id:
            query = query.eq("client_id", str(client_id))
        if lead_id:
            query = query.eq("lead_id", str(lead_id))
        if opportunity_type:
            query = query.eq("opportunity_type", opportunity_type)
        if stage:
            query = query.eq("opportunity_stage", stage)
        if outcome:
            query = query.eq("outcome", outcome)

        # Apply sorting
        order_by = sort_by if sort_by else "created_at"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        opportunities = response.data if response.data else []
        total = response.count if hasattr(response, "count") else len(opportunities)

        # Enrich with client/lead names
        enriched_opportunities = []
        for bo in opportunities:
            enriched = bo.copy()
            if bo.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", bo["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            if bo.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", bo["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    enriched["lead_name"] = lead_resp.data.get("name")
            # Map additional_info to notes for response
            if "additional_info" in enriched:
                enriched["notes"] = enriched.pop("additional_info")
            enriched_opportunities.append(enriched)

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "opportunities": enriched_opportunities,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_opportunity(self, data: BOCreate) -> Dict[str, Any]:
        """Create a new business opportunity."""
        # Validate that either client_id or lead_id is provided
        if not data.client_id and not data.lead_id:
            raise ValueError("Either client_id or lead_id must be provided")

        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)

        # Map notes to additional_info (database uses additional_info)
        if "notes" in insert_data:
            insert_data["additional_info"] = insert_data.pop("notes")

        # Ensure due_date is set (required by schema)
        if not insert_data.get("due_date"):
            insert_data["due_date"] = date.today().isoformat()

        # Ensure opportunity_source is set (required by schema)
        if not insert_data.get("opportunity_source"):
            insert_data["opportunity_source"] = "client_servicing"

        response = supabase.table("business_opportunities").insert(insert_data).execute()
        if response.data:
            opportunity = response.data[0]
            # Map additional_info back to notes for response
            if "additional_info" in opportunity:
                opportunity["notes"] = opportunity.pop("additional_info")
            return opportunity
        raise Exception("Failed to create business opportunity")

    async def get_opportunity(self, bo_id: UUID) -> Optional[Dict[str, Any]]:
        """Get business opportunity by ID."""
        response = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("id", str(bo_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            opportunity = response.data[0]
            # Enrich with client/lead names
            if opportunity.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", opportunity["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    opportunity["client_name"] = client_resp.data.get("name")
            if opportunity.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", opportunity["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    opportunity["lead_name"] = lead_resp.data.get("name")
            # Map additional_info to notes
            if "additional_info" in opportunity:
                opportunity["notes"] = opportunity.pop("additional_info")
            return opportunity
        return None

    async def update_opportunity(
        self, bo_id: UUID, data: BOUpdate
    ) -> Dict[str, Any]:
        """Update business opportunity."""
        # Get existing opportunity
        existing = await self.get_opportunity(bo_id)
        if not existing:
            raise ValueError("Business opportunity not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Map notes to additional_info
        if "notes" in update_data:
            update_data["additional_info"] = update_data.pop("notes")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("business_opportunities")
            .update(update_data)
            .eq("id", str(bo_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            opportunity = response.data[0]
            # Map additional_info back to notes
            if "additional_info" in opportunity:
                opportunity["notes"] = opportunity.pop("additional_info")
            return opportunity
        raise Exception("Failed to update business opportunity")

    async def delete_opportunity(self, bo_id: UUID) -> None:
        """Soft delete business opportunity."""
        # Check if opportunity exists
        existing = await self.get_opportunity(bo_id)
        if not existing:
            raise ValueError("Business opportunity not found")

        # Note: Schema doesn't show is_deleted for business_opportunities
        # Using hard delete for now, but can be changed to soft delete if column is added
        response = (
            supabase.table("business_opportunities")
            .delete()
            .eq("id", str(bo_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Failed to delete business opportunity")

    async def update_outcome(
        self, bo_id: UUID, data: BOOutcomeUpdate
    ) -> Dict[str, Any]:
        """Update business opportunity outcome and calculate TAT."""
        # Get existing opportunity
        existing = await self.get_opportunity(bo_id)
        if not existing:
            raise ValueError("Business opportunity not found")

        # Calculate TAT days (outcome_date - created_at)
        created_at_str = existing.get("created_at")
        if created_at_str:
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            else:
                created_at = created_at_str
            outcome_date_dt = datetime.combine(data.outcome_date, datetime.min.time())
            tat_days = (outcome_date_dt.date() - created_at.date()).days
        else:
            tat_days = None

        # Prepare update data
        update_data = {
            "outcome": data.outcome.value,
            "outcome_date": data.outcome_date.isoformat(),
            "tat_days": tat_days,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if data.outcome_amount is not None:
            update_data["outcome_amount"] = data.outcome_amount

        # Update notes if provided
        if data.notes:
            update_data["additional_info"] = data.notes

        response = (
            supabase.table("business_opportunities")
            .update(update_data)
            .eq("id", str(bo_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            opportunity = response.data[0]
            # Map additional_info back to notes
            if "additional_info" in opportunity:
                opportunity["notes"] = opportunity.pop("additional_info")
            return opportunity
        raise Exception("Failed to update business opportunity outcome")

    async def get_pipeline(self) -> BOPipelineResponse:
        """Get pipeline grouped by stage."""
        # Get all open opportunities (outcome = 'open')
        response = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "open")
            .order("created_at", desc=False)
            .execute()
        )

        opportunities = response.data if response.data else []

        # Enrich opportunities with client/lead names
        enriched_opportunities = []
        for bo in opportunities:
            enriched = bo.copy()
            if bo.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", bo["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            if bo.get("lead_id"):
                lead_resp = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", bo["lead_id"])
                    .single()
                    .execute()
                )
                if lead_resp.data:
                    enriched["lead_name"] = lead_resp.data.get("name")
            # Map additional_info to notes
            if "additional_info" in enriched:
                enriched["notes"] = enriched.pop("additional_info")
            enriched_opportunities.append(enriched)

        # Group by stage
        stages_map = {
            "identified": [],
            "inbound": [],
            "proposed": [],
        }

        for bo in enriched_opportunities:
            stage = bo.get("opportunity_stage", "identified")
            if stage in stages_map:
                stages_map[stage].append(bo)

        # Calculate totals per stage
        stages = []
        for stage_name, stage_opportunities in stages_map.items():
            count = len(stage_opportunities)
            total_amount = sum(
                float(bo.get("expected_amount", 0) or 0) for bo in stage_opportunities
            )
            # Convert to BOResponse objects
            bo_responses = [BOResponse(**bo) for bo in stage_opportunities]
            stages.append(
                BOPipelineStage(
                    stage=stage_name,
                    count=count,
                    total_amount=total_amount,
                    opportunities=bo_responses,
                )
            )

        # Get won/lost totals
        won_response = (
            supabase.table("business_opportunities")
            .select("outcome_amount")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "won")
            .execute()
        )
        won_opportunities = won_response.data if won_response.data else []
        total_won = len(won_opportunities)
        total_won_amount = sum(
            float(bo.get("outcome_amount", 0) or 0) for bo in won_opportunities
        )

        lost_response = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "lost")
            .execute()
        )
        total_lost = len(lost_response.data) if lost_response.data else 0

        # Calculate total open
        total_open = len(enriched_opportunities)
        total_open_amount = sum(
            float(bo.get("expected_amount", 0) or 0) for bo in enriched_opportunities
        )

        return BOPipelineResponse(
            stages=stages,
            total_open=total_open,
            total_open_amount=total_open_amount,
            total_won=total_won,
            total_won_amount=total_won_amount,
            total_lost=total_lost,
        )

    async def update_stage(
        self, bo_id: UUID, new_stage: str, notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update business opportunity stage."""
        # Get existing opportunity
        existing = await self.get_opportunity(bo_id)
        if not existing:
            raise ValueError("Business opportunity not found")

        update_data = {
            "opportunity_stage": new_stage,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Update notes if provided
        if notes:
            update_data["additional_info"] = notes

        response = (
            supabase.table("business_opportunities")
            .update(update_data)
            .eq("id", str(bo_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            opportunity = response.data[0]
            # Map additional_info back to notes
            if "additional_info" in opportunity:
                opportunity["notes"] = opportunity.pop("additional_info")
            return opportunity
        raise Exception("Failed to update business opportunity stage")
