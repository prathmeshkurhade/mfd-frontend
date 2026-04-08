"""Search Service for global search across entities."""

from typing import Any, Dict, List
from uuid import UUID

from app.database import supabase


class SearchService:
    """Service for searching across multiple entities."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def global_search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search across all entities."""
        # Search each entity type
        clients = await self.search_clients(query, limit=5)
        leads = await self.search_leads(query, limit=5)
        tasks = await self.search_tasks(query, limit=5)
        touchpoints = await self.search_touchpoints(query, limit=5)
        goals = await self.search_goals(query, limit=5)

        total = (
            len(clients) + len(leads) + len(tasks) + len(touchpoints) + len(goals)
        )

        return {
            "clients": clients,
            "leads": leads,
            "tasks": tasks,
            "touchpoints": touchpoints,
            "goals": goals,
            "total": total,
        }

    async def search_clients(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search clients by name, phone, email, or area."""
        search_pattern = f"%{query}%"

        response = (
            supabase.table("clients")
            .select("id, name, phone, email, area, total_aum, sip")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .or_(
                f"name.ilike.{search_pattern},"
                f"phone.ilike.{search_pattern},"
                f"email.ilike.{search_pattern},"
                f"area.ilike.{search_pattern}"
            )
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def search_leads(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search leads by name, phone, or email."""
        search_pattern = f"%{query}%"

        response = (
            supabase.table("leads")
            .select("id, name, phone, email, status, source")
            .eq("user_id", str(self.user_id))
            .or_(
                f"name.ilike.{search_pattern},"
                f"phone.ilike.{search_pattern},"
                f"email.ilike.{search_pattern}"
            )
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def search_tasks(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search tasks by title or description."""
        search_pattern = f"%{query}%"

        response = (
            supabase.table("tasks")
            .select("id, description, due_date, status, priority")
            .eq("user_id", str(self.user_id))
            .ilike("description", search_pattern)
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def search_touchpoints(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search touchpoints by agenda, notes, or mom_text."""
        search_pattern = f"%{query}%"

        # Note: Using 'purpose' instead of 'agenda' as per database schema
        response = (
            supabase.table("touchpoints")
            .select("id, client_id, scheduled_date, interaction_type, purpose, status")
            .eq("user_id", str(self.user_id))
            .or_(
                f"purpose.ilike.{search_pattern},"
                f"mom_text.ilike.{search_pattern}"
            )
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def search_goals(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search goals by goal_name."""
        search_pattern = f"%{query}%"

        response = (
            supabase.table("goals")
            .select("id, goal_name, goal_type, target_amount, status, progress_percent")
            .eq("user_id", str(self.user_id))
            .ilike("goal_name", search_pattern)
            .limit(limit)
            .execute()
        )

        return response.data if response.data else []

    async def get_recent_searches(self, limit: int = 10) -> List[str]:
        """
        Get user's recent search queries.
        
        NOTE: This is an optional feature that requires a search_history table
        to be created in the database. Currently returns empty list.
        """
        # TODO: Implement search history tracking
        # Would require creating a search_history table to store queries
        # response = (
        #     supabase.table("search_history")
        #     .select("query")
        #     .eq("user_id", str(self.user_id))
        #     .order("created_at", desc=True)
        #     .limit(limit)
        #     .execute()
        # )
        # return [item["query"] for item in response.data] if response.data else []

        return []
