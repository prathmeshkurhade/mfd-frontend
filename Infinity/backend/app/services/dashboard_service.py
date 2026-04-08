"""Dashboard Service for stats and analytics."""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from uuid import UUID

from app.database import supabase


class DashboardService:
    """Service for dashboard statistics and overview."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics."""
        # Total clients
        clients_response = (
            supabase.table("clients")
            .select("id, total_aum, sip", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .execute()
        )
        total_clients = clients_response.count if clients_response.count else 0

        # Calculate total AUM and SIP
        total_aum = 0
        total_sip = 0
        if clients_response.data:
            for client in clients_response.data:
                total_aum += client.get("total_aum") or 0
                total_sip += client.get("sip") or 0

        # Total leads
        leads_response = (
            supabase.table("leads")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .execute()
        )
        total_leads = leads_response.count if leads_response.count else 0

        # Leads this month
        first_day_of_month = date.today().replace(day=1)
        leads_this_month_response = (
            supabase.table("leads")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .gte("created_at", first_day_of_month.isoformat())
            .execute()
        )
        leads_this_month = (
            leads_this_month_response.count if leads_this_month_response.count else 0
        )

        # Conversions this month (clients converted from leads)
        conversions_response = (
            supabase.table("clients")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .not_.is_("converted_from_lead_id", "null")
            .gte("created_at", first_day_of_month.isoformat())
            .execute()
        )
        conversions_this_month = (
            conversions_response.count if conversions_response.count else 0
        )

        # Open opportunities
        open_bos_response = (
            supabase.table("business_opportunities")
            .select("id, expected_amount", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "open")
            .execute()
        )
        open_opportunities_count = (
            open_bos_response.count if open_bos_response.count else 0
        )

        open_opportunities_value = 0
        if open_bos_response.data:
            for bo in open_bos_response.data:
                open_opportunities_value += bo.get("expected_amount") or 0

        # Tasks pending today
        today = date.today()
        tasks_today_response = (
            supabase.table("tasks")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "pending")
            .execute()
        )
        tasks_pending_today = tasks_today_response.count if tasks_today_response.count else 0

        # Tasks overdue
        tasks_overdue_response = (
            supabase.table("tasks")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .lt("due_date", today.isoformat())
            .eq("status", "pending")
            .execute()
        )
        tasks_overdue = tasks_overdue_response.count if tasks_overdue_response.count else 0

        # Touchpoints this week
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        touchpoints_week_response = (
            supabase.table("touchpoints")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .gte("scheduled_date", week_start.isoformat())
            .lte("scheduled_date", week_end.isoformat())
            .execute()
        )
        touchpoints_this_week = (
            touchpoints_week_response.count if touchpoints_week_response.count else 0
        )

        # Upcoming birthdays (next 7 days)
        next_7_days = today + timedelta(days=7)
        
        # Get all clients with birthdate
        all_clients_response = (
            supabase.table("clients")
            .select("id, name, birthdate")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .not_.is_("birthdate", "null")
            .execute()
        )

        upcoming_birthdays = 0
        if all_clients_response.data:
            for client in all_clients_response.data:
                if client.get("birthdate"):
                    try:
                        birthdate = datetime.fromisoformat(
                            client["birthdate"].replace("Z", "+00:00")
                        ).date()
                        
                        # Calculate next birthday
                        this_year_birthday = birthdate.replace(year=today.year)
                        if this_year_birthday < today:
                            next_birthday = birthdate.replace(year=today.year + 1)
                        else:
                            next_birthday = this_year_birthday
                        
                        # Check if within next 7 days
                        days_until = (next_birthday - today).days
                        if 0 <= days_until <= 7:
                            upcoming_birthdays += 1
                    except Exception:
                        continue

        return {
            "total_clients": total_clients,
            "total_leads": total_leads,
            "leads_this_month": leads_this_month,
            "conversions_this_month": conversions_this_month,
            "total_aum": round(total_aum, 2),
            "total_sip": round(total_sip, 2),
            "open_opportunities_count": open_opportunities_count,
            "open_opportunities_value": round(open_opportunities_value, 2),
            "tasks_pending_today": tasks_pending_today,
            "tasks_overdue": tasks_overdue,
            "touchpoints_this_week": touchpoints_this_week,
            "upcoming_birthdays": upcoming_birthdays,
        }

    async def get_today_summary(self, target_date: date = None) -> Dict[str, Any]:
        """Get summary for a given date (defaults to today)."""
        today = target_date or date.today()

        # Tasks pending today
        tasks_response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today.isoformat())
            .eq("status", "pending")
            .execute()
        )
        tasks_pending = tasks_response.data if tasks_response.data else []

        # Tasks completed today
        tasks_completed_response = (
            supabase.table("tasks")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("status", "completed")
            .gte("completed_at", today.isoformat())
            .execute()
        )
        tasks_completed_today = (
            tasks_completed_response.count if tasks_completed_response.count else 0
        )

        # Leads to follow up today
        leads_response = (
            supabase.table("leads")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", today.isoformat())
            .in_("status", ["follow_up", "meeting_scheduled"])
            .execute()
        )
        leads_to_followup = leads_response.data if leads_response.data else []

        # Touchpoints today
        touchpoints_response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("scheduled_date", today.isoformat())
            .execute()
        )
        touchpoints_today = touchpoints_response.data if touchpoints_response.data else []

        # Birthdays today
        all_clients_response = (
            supabase.table("clients")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .not_.is_("birthdate", "null")
            .execute()
        )

        birthdays_today = []
        if all_clients_response.data:
            for client in all_clients_response.data:
                if client.get("birthdate"):
                    try:
                        birthdate = datetime.fromisoformat(
                            client["birthdate"].replace("Z", "+00:00")
                        ).date()
                        if birthdate.month == today.month and birthdate.day == today.day:
                            birthdays_today.append(client)
                    except Exception:
                        continue

        return {
            "tasks_pending": tasks_pending,
            "tasks_completed_today": tasks_completed_today,
            "leads_to_followup": leads_to_followup,
            "touchpoints_today": touchpoints_today,
            "birthdays_today": birthdays_today,
        }

    async def get_calendar_events(self, date_from: date, date_to: date) -> List[Dict[str, Any]]:
        """Get all calendar events (tasks, touchpoints, leads, opportunities) for a date range."""
        events: List[Dict[str, Any]] = []
        date_to_str = date_to.isoformat()

        # NOTE: client_name / lead_name are NOT real DB columns — they are
        # enriched in Python. Use client_id / lead_id and resolve names via
        # a lookup cache to avoid N+1 queries.

        # Collect client/lead IDs for batch name resolution
        client_ids: set = set()
        lead_ids: set = set()

        # Tasks in range (select only real DB columns — no "title", use "description")
        tasks_response = (
            supabase.table("tasks")
            .select("id, description, due_date, due_time, status, priority, client_id, lead_id, all_day")
            .eq("user_id", str(self.user_id))
            .gte("due_date", date_from.isoformat())
            .execute()
        )
        raw_tasks = [t for t in (tasks_response.data or []) if t["due_date"] <= date_to_str]

        # Touchpoints in range (no "agenda", use "purpose")
        tp_response = (
            supabase.table("touchpoints")
            .select("id, interaction_type, scheduled_date, scheduled_time, status, location, purpose, client_id, lead_id")
            .eq("user_id", str(self.user_id))
            .gte("scheduled_date", date_from.isoformat())
            .execute()
        )
        raw_tps = [tp for tp in (tp_response.data or []) if tp["scheduled_date"] <= date_to_str]

        # Leads with follow-up in range
        leads_response = (
            supabase.table("leads")
            .select("id, name, phone, status, scheduled_date")
            .eq("user_id", str(self.user_id))
            .gte("scheduled_date", date_from.isoformat())
            .in_("status", ["follow_up", "meeting_scheduled"])
            .execute()
        )
        raw_leads = [l for l in (leads_response.data or []) if l["scheduled_date"] <= date_to_str]

        # Business opportunities with due date in range
        bo_response = (
            supabase.table("business_opportunities")
            .select("id, opportunity_type, expected_amount, due_date, outcome, client_id, lead_id")
            .eq("user_id", str(self.user_id))
            .not_.is_("due_date", "null")
            .gte("due_date", date_from.isoformat())
            .execute()
        )
        raw_bos = [bo for bo in (bo_response.data or []) if bo["due_date"] <= date_to_str]

        # Collect all client/lead IDs for batch lookup
        for item in raw_tasks + raw_tps + raw_bos:
            if item.get("client_id"):
                client_ids.add(item["client_id"])
            if item.get("lead_id"):
                lead_ids.add(item["lead_id"])

        # Batch resolve names
        client_names: Dict[str, str] = {}
        lead_names: Dict[str, str] = {}

        if client_ids:
            clients_resp = (
                supabase.table("clients")
                .select("id, name")
                .in_("id", list(client_ids))
                .execute()
            )
            for c in (clients_resp.data or []):
                client_names[c["id"]] = c.get("name", "Unknown")

        if lead_ids:
            leads_resp = (
                supabase.table("leads")
                .select("id, name")
                .in_("id", list(lead_ids))
                .execute()
            )
            for l in (leads_resp.data or []):
                lead_names[l["id"]] = l.get("name", "Unknown")

        def _name(item: Dict) -> str:
            return client_names.get(item.get("client_id", ""), "") or lead_names.get(item.get("lead_id", ""), "") or "Unknown"

        # Build events
        for t in raw_tasks:
            events.append({
                "id": t["id"],
                "title": t.get("description") or "Untitled Task",
                "date": t["due_date"],
                "time": t.get("due_time"),
                "type": "task",
                "status": t.get("status", "pending"),
                "priority": t.get("priority"),
                "all_day": t.get("all_day", True),
                "client_name": client_names.get(t.get("client_id", "")),
                "lead_name": lead_names.get(t.get("lead_id", "")),
            })

        for tp in raw_tps:
            events.append({
                "id": tp["id"],
                "title": f"{(tp.get('interaction_type') or 'meeting').replace('_', ' ').title()} - {_name(tp)}",
                "date": tp["scheduled_date"],
                "time": tp.get("scheduled_time"),
                "type": "touchpoint",
                "status": tp.get("status", "scheduled"),
                "location": tp.get("location"),
                "agenda": tp.get("purpose"),
                "client_name": client_names.get(tp.get("client_id", "")),
                "lead_name": lead_names.get(tp.get("lead_id", "")),
                "interaction_type": tp.get("interaction_type"),
            })

        for lead in raw_leads:
            events.append({
                "id": lead["id"],
                "title": f"Follow-up: {lead.get('name', 'Unknown')}",
                "date": lead["scheduled_date"],
                "time": None,
                "type": "lead",
                "status": lead.get("status", "follow_up"),
                "client_name": None,
                "lead_name": lead.get("name"),
            })

        for bo in raw_bos:
            events.append({
                "id": bo["id"],
                "title": f"{(bo.get('opportunity_type') or 'opportunity').replace('_', ' ').title()} - {_name(bo)}",
                "date": bo["due_date"],
                "time": None,
                "type": "opportunity",
                "status": bo.get("outcome", "open"),
                "client_name": client_names.get(bo.get("client_id", "")),
                "lead_name": lead_names.get(bo.get("lead_id", "")),
                "expected_amount": bo.get("expected_amount"),
            })

        return events

    async def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get business opportunity pipeline summary."""
        # Get all open opportunities
        bos_response = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "open")
            .execute()
        )

        bos = bos_response.data if bos_response.data else []

        # Group by stage
        by_stage = {"identified": 0, "inbound": 0, "proposed": 0}
        by_type = {}
        total_value = 0

        for bo in bos:
            stage = bo.get("opportunity_stage", "identified")
            bo_type = bo.get("opportunity_type", "other")
            amount = bo.get("expected_amount") or 0

            by_stage[stage] = by_stage.get(stage, 0) + 1
            by_type[bo_type] = by_type.get(bo_type, 0) + amount
            total_value += amount

        # Won this month
        first_day_of_month = date.today().replace(day=1)
        won_response = (
            supabase.table("business_opportunities")
            .select("outcome_amount")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "won")
            .gte("outcome_date", first_day_of_month.isoformat())
            .execute()
        )

        won_this_month = 0
        if won_response.data:
            for bo in won_response.data:
                won_this_month += bo.get("outcome_amount") or 0

        # Lost this month
        lost_response = (
            supabase.table("business_opportunities")
            .select("expected_amount")
            .eq("user_id", str(self.user_id))
            .eq("outcome", "lost")
            .gte("outcome_date", first_day_of_month.isoformat())
            .execute()
        )

        lost_this_month = 0
        if lost_response.data:
            for bo in lost_response.data:
                lost_this_month += bo.get("expected_amount") or 0

        return {
            "by_stage": by_stage,
            "by_type": by_type,
            "total_value": round(total_value, 2),
            "won_this_month": round(won_this_month, 2),
            "lost_this_month": round(lost_this_month, 2),
        }

    async def get_conversion_stats(self, period: str = "month") -> Dict[str, Any]:
        """Get lead conversion statistics."""
        # Calculate date range based on period
        today = date.today()
        if period == "month":
            start_date = today.replace(day=1)
        elif period == "quarter":
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = today.replace(month=quarter_start_month, day=1)
        elif period == "year":
            start_date = today.replace(month=1, day=1)
        else:
            start_date = today.replace(day=1)

        # Leads created in period
        leads_response = (
            supabase.table("leads")
            .select("id", count="exact")
            .eq("user_id", str(self.user_id))
            .gte("created_at", start_date.isoformat())
            .execute()
        )
        leads_created = leads_response.count if leads_response.count else 0

        # Leads converted in period
        converted_response = (
            supabase.table("clients")
            .select("id, tat_days")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .not_.is_("converted_from_lead_id", "null")
            .gte("created_at", start_date.isoformat())
            .execute()
        )
        leads_converted = len(converted_response.data) if converted_response.data else 0

        # Calculate conversion rate
        conversion_rate = (
            (leads_converted / leads_created * 100) if leads_created > 0 else 0
        )

        # Calculate average TAT days
        average_tat_days = 0
        if converted_response.data:
            tat_values = [
                client.get("tat_days")
                for client in converted_response.data
                if client.get("tat_days") is not None
            ]
            if tat_values:
                average_tat_days = sum(tat_values) / len(tat_values)

        return {
            "period": period,
            "leads_created": leads_created,
            "leads_converted": leads_converted,
            "conversion_rate": round(conversion_rate, 2),
            "average_tat_days": round(average_tat_days, 1),
        }

    async def get_client_growth(self, period: str = "year") -> List[Dict[str, Any]]:
        """Get client growth data by month."""
        today = date.today()

        # Calculate start date based on period
        if period == "year":
            start_date = today.replace(month=1, day=1)
            months = 12
        elif period == "quarter":
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = today.replace(month=quarter_start_month, day=1)
            months = 3
        else:
            start_date = today.replace(day=1)
            months = 1

        # Get all clients created in the period
        clients_response = (
            supabase.table("clients")
            .select("created_at, total_aum")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .gte("created_at", start_date.isoformat())
            .execute()
        )

        # Group by month
        monthly_data = {}
        month_names = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        # Initialize all months
        current = start_date
        for _ in range(months):
            month_key = f"{month_names[current.month - 1]} {current.year}"
            monthly_data[month_key] = {"clients": 0, "aum": 0}
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Populate with actual data
        if clients_response.data:
            for client in clients_response.data:
                try:
                    created_date = datetime.fromisoformat(
                        client["created_at"].replace("Z", "+00:00")
                    ).date()
                    month_key = f"{month_names[created_date.month - 1]} {created_date.year}"
                    
                    if month_key in monthly_data:
                        monthly_data[month_key]["clients"] += 1
                        monthly_data[month_key]["aum"] += client.get("total_aum") or 0
                except Exception:
                    continue

        # Convert to list format
        result = []
        for month_key, data in monthly_data.items():
            result.append(
                {
                    "month": month_key,
                    "clients": data["clients"],
                    "aum": round(data["aum"], 2),
                }
            )

        return result
