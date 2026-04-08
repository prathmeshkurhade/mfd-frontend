"""Data Export Service for Excel/CSV export."""

from datetime import date
from io import BytesIO
from typing import Any, Dict, Optional
from uuid import UUID

import pandas as pd
from openpyxl import Workbook

from app.database import supabase


class ExportService:
    """Service for exporting data to Excel/CSV files."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def export_clients_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """Export clients to Excel."""
        # Query clients
        query = (
            supabase.table("clients")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
        )

        # Apply filters if provided
        if filters:
            if filters.get("area"):
                query = query.eq("area", filters["area"])
            if filters.get("risk_profile"):
                query = query.eq("risk_profile", filters["risk_profile"])
            if filters.get("occupation"):
                query = query.eq("occupation", filters["occupation"])

        response = query.execute()
        clients = response.data if response.data else []

        # Calculate age for each client
        for client in clients:
            if client.get("birthdate"):
                try:
                    birthdate = pd.to_datetime(client["birthdate"]).date()
                    today = date.today()
                    age = (
                        today.year
                        - birthdate.year
                        - ((today.month, today.day) < (birthdate.month, birthdate.day))
                    )
                    client["age"] = age
                except Exception:
                    client["age"] = None
            else:
                client["age"] = None

        # Create DataFrame
        df = pd.DataFrame(clients)

        # Select and order columns
        columns = [
            "name",
            "phone",
            "email",
            "birthdate",
            "age",
            "gender",
            "marital_status",
            "occupation",
            "income_group",
            "area",
            "total_aum",
            "sip",
            "risk_profile",
            "source",
            "created_at",
        ]

        # Only include columns that exist in the data
        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Clients")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_leads_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """Export leads to Excel."""
        # Query leads
        query = (
            supabase.table("leads")
            .select("*")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters if provided
        if filters:
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("source"):
                query = query.eq("source", filters["source"])

        response = query.execute()
        leads = response.data if response.data else []

        # Create DataFrame
        df = pd.DataFrame(leads)

        # Select and order columns
        columns = [
            "name",
            "phone",
            "email",
            "gender",
            "marital_status",
            "occupation",
            "income_group",
            "area",
            "source",
            "status",
            "scheduled_date",
            "scheduled_time",
            "notes",
            "created_at",
        ]

        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Leads")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_tasks_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """Export tasks to Excel."""
        # Query tasks
        query = supabase.table("tasks").select("*").eq("user_id", str(self.user_id))

        # Apply filters if provided
        if filters:
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("priority"):
                query = query.eq("priority", filters["priority"])

        response = query.execute()
        tasks = response.data if response.data else []

        # Enrich with client/lead names
        for task in tasks:
            if task.get("client_id"):
                client_response = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", task["client_id"])
                    .execute()
                )
                if client_response.data:
                    task["client_name"] = client_response.data[0]["name"]

            if task.get("lead_id"):
                lead_response = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", task["lead_id"])
                    .execute()
                )
                if lead_response.data:
                    task["lead_name"] = lead_response.data[0]["name"]

        # Create DataFrame
        df = pd.DataFrame(tasks)

        # Select and order columns
        columns = [
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "due_time",
            "client_name",
            "lead_name",
            "created_at",
            "completed_at",
        ]

        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Tasks")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_touchpoints_to_excel(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export touchpoints to Excel."""
        # Query touchpoints
        query = (
            supabase.table("touchpoints").select("*").eq("user_id", str(self.user_id))
        )

        # Apply filters if provided
        if filters:
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("interaction_type"):
                query = query.eq("interaction_type", filters["interaction_type"])

        response = query.execute()
        touchpoints = response.data if response.data else []

        # Enrich with client names
        for touchpoint in touchpoints:
            if touchpoint.get("client_id"):
                client_response = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", touchpoint["client_id"])
                    .execute()
                )
                if client_response.data:
                    touchpoint["client_name"] = client_response.data[0]["name"]

        # Create DataFrame
        df = pd.DataFrame(touchpoints)

        # Select and order columns (use 'purpose' from DB, rename to 'agenda' for display)
        columns = [
            "client_name",
            "interaction_type",
            "purpose",
            "scheduled_date",
            "scheduled_time",
            "status",
            "outcome",
            "notes",
            "mom_text",
            "created_at",
        ]

        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Rename purpose to agenda for export
        if "purpose" in df.columns:
            df = df.rename(columns={"purpose": "agenda"})

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Touchpoints")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_goals_to_excel(self, filters: Optional[Dict[str, Any]] = None) -> bytes:
        """Export goals to Excel."""
        # Query goals
        query = supabase.table("goals").select("*").eq("user_id", str(self.user_id))

        # Apply filters if provided
        if filters:
            if filters.get("status"):
                query = query.eq("status", filters["status"])
            if filters.get("goal_type"):
                query = query.eq("goal_type", filters["goal_type"])

        response = query.execute()
        goals = response.data if response.data else []

        # Enrich with client names
        for goal in goals:
            if goal.get("client_id"):
                client_response = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", goal["client_id"])
                    .execute()
                )
                if client_response.data:
                    goal["client_name"] = client_response.data[0]["name"]

        # Create DataFrame
        df = pd.DataFrame(goals)

        # Select and order columns
        columns = [
            "client_name",
            "goal_name",
            "goal_type",
            "target_amount",
            "current_investment",
            "monthly_sip",
            "lumpsum_investment",
            "target_date",
            "progress_percent",
            "status",
            "created_at",
        ]

        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Goals")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_opportunities_to_excel(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Export business opportunities to Excel."""
        # Query opportunities
        query = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters if provided
        if filters:
            if filters.get("opportunity_stage"):
                query = query.eq("opportunity_stage", filters["opportunity_stage"])
            if filters.get("opportunity_type"):
                query = query.eq("opportunity_type", filters["opportunity_type"])

        response = query.execute()
        opportunities = response.data if response.data else []

        # Enrich with client names
        for opp in opportunities:
            if opp.get("client_id"):
                client_response = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", opp["client_id"])
                    .execute()
                )
                if client_response.data:
                    opp["client_name"] = client_response.data[0]["name"]

        # Create DataFrame
        df = pd.DataFrame(opportunities)

        # Select and order columns (map additional_info to notes for export)
        columns = [
            "client_name",
            "opportunity_type",
            "opportunity_stage",
            "estimated_amount",
            "probability_percent",
            "opportunity_source",
            "outcome",
            "outcome_date",
            "outcome_amount",
            "additional_info",
            "created_at",
        ]

        columns = [col for col in columns if col in df.columns]
        df = df[columns]

        # Rename additional_info to notes for export
        if "additional_info" in df.columns:
            df = df.rename(columns={"additional_info": "notes"})

        # Convert to Excel
        buffer = BytesIO()
        df.to_excel(buffer, index=False, sheet_name="Business Opportunities")
        buffer.seek(0)
        return buffer.getvalue()

    async def export_all_data(self) -> bytes:
        """Export all data to a multi-sheet Excel workbook."""
        # Get all data
        clients_bytes = await self.export_clients_to_excel()
        leads_bytes = await self.export_leads_to_excel()
        tasks_bytes = await self.export_tasks_to_excel()
        touchpoints_bytes = await self.export_touchpoints_to_excel()
        goals_bytes = await self.export_goals_to_excel()
        opportunities_bytes = await self.export_opportunities_to_excel()

        # Read each into DataFrame
        clients_df = pd.read_excel(BytesIO(clients_bytes))
        leads_df = pd.read_excel(BytesIO(leads_bytes))
        tasks_df = pd.read_excel(BytesIO(tasks_bytes))
        touchpoints_df = pd.read_excel(BytesIO(touchpoints_bytes))
        goals_df = pd.read_excel(BytesIO(goals_bytes))
        opportunities_df = pd.read_excel(BytesIO(opportunities_bytes))

        # Create multi-sheet workbook
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            clients_df.to_excel(writer, sheet_name="Clients", index=False)
            leads_df.to_excel(writer, sheet_name="Leads", index=False)
            tasks_df.to_excel(writer, sheet_name="Tasks", index=False)
            touchpoints_df.to_excel(writer, sheet_name="Touchpoints", index=False)
            goals_df.to_excel(writer, sheet_name="Goals", index=False)
            opportunities_df.to_excel(
                writer, sheet_name="Business Opportunities", index=False
            )

        buffer.seek(0)
        return buffer.getvalue()
