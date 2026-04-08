from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase_admin as supabase
from app.models.goal import (
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    GoalUpdate,
    GoalWithSubgoals,
)


class GoalService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def _calculate_progress(self, current: float, target: float) -> float:
        """Calculate progress percentage."""
        if target <= 0:
            return 0.0
        progress = (current / target) * 100
        return min(progress, 100.0)  # Cap at 100%

    async def list_goals(
        self,
        page: int = 1,
        limit: int = 20,
        client_id: Optional[UUID] = None,
        goal_type: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List goals with filters and pagination."""
        query = (
            supabase.table("goals")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters
        if client_id:
            query = query.eq("client_id", str(client_id))
        if goal_type:
            query = query.eq("goal_type", goal_type)
        if status:
            query = query.eq("status", status)

        # Apply sorting
        order_by = sort_by if sort_by else "created_at"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        goals = response.data if response.data else []
        total = response.count if hasattr(response, "count") else len(goals)

        # Enrich with client names
        enriched_goals = []
        for goal in goals:
            enriched = goal.copy()
            if goal.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", goal["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            enriched_goals.append(enriched)

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "goals": enriched_goals,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_goal(self, data: GoalCreate) -> Dict[str, Any]:
        """Create a new goal."""
        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)

        # Calculate progress percentage
        current = insert_data.get("current_investment", 0)
        target = insert_data.get("target_amount", 0)
        insert_data["progress_percent"] = self._calculate_progress(current, target)

        # Set default status if not provided
        if "status" not in insert_data:
            insert_data["status"] = "active"

        # Convert non-serializable values to strings
        for key, value in list(insert_data.items()):
            if hasattr(value, "value"):
                insert_data[key] = value.value
            elif isinstance(value, UUID):
                insert_data[key] = str(value)
            elif isinstance(value, (date, datetime)):
                insert_data[key] = value.isoformat()

        # Convert products to JSONB if present
        if "products" in insert_data and insert_data["products"]:
            insert_data["products"] = [p.model_dump() if hasattr(p, "model_dump") else p for p in insert_data["products"]]

        response = supabase.table("goals").insert(insert_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create goal")

    async def get_goal(self, goal_id: UUID) -> Optional[Dict[str, Any]]:
        """Get goal by ID."""
        response = (
            supabase.table("goals")
            .select("*")
            .eq("id", str(goal_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            goal = response.data[0]
            # Enrich with client name
            if goal.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", goal["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    goal["client_name"] = client_resp.data.get("name")
            return goal
        return None

    async def update_goal(
        self, goal_id: UUID, data: GoalUpdate
    ) -> Dict[str, Any]:
        """Update goal."""
        # Get existing goal
        existing = await self.get_goal(goal_id)
        if not existing:
            raise ValueError("Goal not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Recalculate progress if investment or target amount changed
        current = update_data.get("current_investment", existing.get("current_investment", 0))
        target = update_data.get("target_amount", existing.get("target_amount", 0))
        update_data["progress_percent"] = self._calculate_progress(current, target)

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("goals")
            .update(update_data)
            .eq("id", str(goal_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        raise Exception("Failed to update goal")

    async def delete_goal(self, goal_id: UUID) -> None:
        """Soft delete goal and its sub-goals."""
        # Check if goal exists
        existing = await self.get_goal(goal_id)
        if not existing:
            raise ValueError("Goal not found")

        # Note: Schema doesn't show is_deleted for goals
        # Using hard delete for now, but can be changed to soft delete if column is added

        # Delete sub-goals first (if this is a parent goal)
        subgoals_response = (
            supabase.table("goals")
            .select("id")
            .eq("user_id", str(self.user_id))
            .eq("parent_goal_id", str(goal_id))
            .execute()
        )
        if subgoals_response.data:
            for subgoal in subgoals_response.data:
                supabase.table("goals").delete().eq("id", subgoal["id"]).execute()

        # Delete the goal itself
        response = (
            supabase.table("goals")
            .delete()
            .eq("id", str(goal_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Failed to delete goal")

    async def get_with_subgoals(
        self, goal_id: UUID
    ) -> GoalWithSubgoals:
        """Get parent goal with all sub-goals."""
        # Get parent goal
        parent = await self.get_goal(goal_id)
        if not parent:
            raise ValueError("Goal not found")

        # Get sub-goals
        subgoals_response = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("parent_goal_id", str(goal_id))
            .order("created_at", desc=False)
            .execute()
        )

        subgoals = subgoals_response.data if subgoals_response.data else []

        # Enrich subgoals with client names
        enriched_subgoals = []
        for subgoal in subgoals:
            enriched = subgoal.copy()
            if subgoal.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", subgoal["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            enriched_subgoals.append(enriched)

        # Calculate totals
        total_target = parent.get("target_amount", 0) + sum(
            sg.get("target_amount", 0) for sg in subgoals
        )
        total_monthly_sip = parent.get("monthly_sip", 0) + sum(
            sg.get("monthly_sip", 0) for sg in subgoals
        )

        return GoalWithSubgoals(
            parent_goal=GoalResponse(**parent),
            sub_goals=[GoalResponse(**sg) for sg in enriched_subgoals],
            total_target=total_target,
            total_monthly_sip=total_monthly_sip,
        )

    async def get_client_goals(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Get all goals for a client."""
        response = (
            supabase.table("goals")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("client_id", str(client_id))
            .order("created_at", desc=False)
            .execute()
        )

        goals = response.data if response.data else []

        # Enrich with client names
        enriched_goals = []
        for goal in goals:
            enriched = goal.copy()
            if goal.get("client_id"):
                client_resp = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", goal["client_id"])
                    .single()
                    .execute()
                )
                if client_resp.data:
                    enriched["client_name"] = client_resp.data.get("name")
            enriched_goals.append(enriched)

        return enriched_goals

    async def update_progress(
        self, goal_id: UUID, current_investment: float
    ) -> Dict[str, Any]:
        """Update current investment and recalculate progress."""
        # Get existing goal
        existing = await self.get_goal(goal_id)
        if not existing:
            raise ValueError("Goal not found")

        target_amount = existing.get("target_amount", 0)
        progress_percent = self._calculate_progress(current_investment, target_amount)

        update_data = {
            "current_investment": current_investment,
            "progress_percent": progress_percent,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = (
            supabase.table("goals")
            .update(update_data)
            .eq("id", str(goal_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        raise Exception("Failed to update goal progress")
