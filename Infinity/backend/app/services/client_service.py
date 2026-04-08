from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.constants.enums import AgeGroupType, AumBracketType, SipBracketType
from app.database import supabase
from app.models.client import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    ConvertLeadRequest,
    DuplicateCheckResponse,
)


class ClientService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def _calculate_age(self, birthdate: Optional[date]) -> Optional[int]:
        """Calculate age from birthdate."""
        if not birthdate:
            return None
        today = date.today()
        age = today.year - birthdate.year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
        return age

    def _calculate_age_group(self, age: Optional[int]) -> Optional[AgeGroupType]:
        """Calculate age group from age."""
        if age is None:
            return None
        if age < 18:
            return AgeGroupType.below_18
        elif age <= 24:
            return AgeGroupType.v18_to_24
        elif age <= 35:
            return AgeGroupType.v25_to_35
        elif age <= 45:
            return AgeGroupType.v36_to_45
        elif age <= 55:
            return AgeGroupType.v46_to_55
        else:
            return AgeGroupType.v56_plus

    def _calculate_aum_bracket(self, aum: Optional[float]) -> Optional[AumBracketType]:
        """Calculate AUM bracket from amount."""
        if aum is None or aum == 0:
            return None
        aum_lakhs = aum / 100000  # Convert to lakhs
        if aum_lakhs < 10:
            return AumBracketType.less_than_10_lakhs
        elif aum_lakhs < 25:
            return AumBracketType.v10_to_25_lakhs
        elif aum_lakhs < 50:
            return AumBracketType.v25_to_50_lakhs
        elif aum_lakhs < 100:
            return AumBracketType.v50_lakhs_to_1_cr
        else:
            return AumBracketType.v1_cr_plus

    def _calculate_sip_bracket(self, sip: Optional[float]) -> Optional[SipBracketType]:
        """Calculate SIP bracket from amount."""
        if sip is None or sip == 0:
            return SipBracketType.zero
        sip_thousands = sip / 1000
        if sip_thousands <= 5:
            return SipBracketType.upto_5k
        elif sip_thousands <= 10:
            return SipBracketType.v5_1k_to_10k
        elif sip_thousands <= 25:
            return SipBracketType.v10_1k_to_25k
        elif sip_thousands <= 50:
            return SipBracketType.v25_1k_to_50k
        elif sip_thousands < 100:
            return SipBracketType.v50_1k_to_1_lakh
        else:
            return SipBracketType.v1_lakh_plus

    async def list_clients(
        self,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        area: Optional[str] = None,
        age_group: Optional[str] = None,
        risk_profile: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """List clients with filters and pagination."""
        query = (
            supabase.table("clients")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
        )

        # Apply search filter
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,phone.ilike.%{search}%"
            )

        # Apply filters
        if area:
            query = query.eq("area", area)
        if age_group:
            query = query.eq("age_group", age_group)
        if risk_profile:
            query = query.eq("risk_profile", risk_profile)

        # Apply sorting
        order_by = sort_by if sort_by else "created_at"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        clients = response.data if response.data else []
        total = response.count if hasattr(response, "count") else len(clients)

        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "clients": clients,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_client(self, data: ClientCreate) -> Dict[str, Any]:
        """Create a new client."""
        # Check for duplicate phone
        duplicate_check = await self.check_duplicate(data.phone)
        if duplicate_check["is_duplicate"]:
            raise ValueError("Client with this phone number already exists")

        # Calculate age and age_group
        age = self._calculate_age(data.birthdate) if data.birthdate else None
        age_group = self._calculate_age_group(age)

        # Calculate brackets
        aum_bracket = self._calculate_aum_bracket(data.aum)
        sip_bracket = self._calculate_sip_bracket(data.sip_amount)

        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)
        insert_data["age"] = age
        insert_data["age_group"] = age_group.value if age_group else None
        insert_data["aum_bracket"] = aum_bracket.value if aum_bracket else None
        insert_data["sip_bracket"] = sip_bracket.value if sip_bracket else None

        # Map API field names to DB column names (pop to avoid unknown column errors)
        insert_data["total_aum"] = insert_data.pop("aum", None) or 0
        insert_data["sip"] = insert_data.pop("sip_amount", None) or 0
        if "referred_by" in insert_data:
            insert_data["sourced_by"] = insert_data.pop("referred_by")

        response = supabase.table("clients").insert(insert_data).execute()
        if response.data:
            return response.data[0]
        raise Exception("Failed to create client")

    async def get_client(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client by ID."""
        response = (
            supabase.table("clients")
            .select("*")
            .eq("id", str(client_id))
            .eq("user_id", str(self.user_id))
            .eq("is_deleted", False)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    async def update_client(
        self, client_id: UUID, data: ClientUpdate
    ) -> Dict[str, Any]:
        """Update client."""
        # Get existing client
        existing = await self.get_client(client_id)
        if not existing:
            raise ValueError("Client not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Recalculate age if birthdate changed
        if "birthdate" in update_data:
            birthdate = data.birthdate  # use the original date object
            age = self._calculate_age(birthdate)
            age_group = self._calculate_age_group(age)
            update_data["age"] = age
            update_data["age_group"] = age_group.value if age_group else None

        # Recalculate brackets if AUM or SIP changed (pop API names, use DB names)
        if "aum" in update_data:
            aum_val = update_data.pop("aum")
            aum_bracket = self._calculate_aum_bracket(aum_val)
            update_data["aum_bracket"] = aum_bracket.value if aum_bracket else None
            update_data["total_aum"] = aum_val or 0

        if "sip_amount" in update_data:
            sip_val = update_data.pop("sip_amount")
            sip_bracket = self._calculate_sip_bracket(sip_val)
            update_data["sip_bracket"] = sip_bracket.value if sip_bracket else None
            update_data["sip"] = sip_val or 0

        # Map API field name to DB column name
        if "referred_by" in update_data:
            update_data["sourced_by"] = update_data.pop("referred_by")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("clients")
            .update(update_data)
            .eq("id", str(client_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        raise Exception("Failed to update client")

    async def delete_client(self, client_id: UUID) -> None:
        """Soft delete client."""
        update_data = {
            "is_deleted": True,
            "deleted_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        response = (
            supabase.table("clients")
            .update(update_data)
            .eq("id", str(client_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Client not found")

    async def get_overview(self, client_id: UUID) -> Dict[str, Any]:
        """Get client overview with related data."""
        client = await self.get_client(client_id)
        if not client:
            raise ValueError("Client not found")

        # Get goals
        goals_response = (
            supabase.table("goals")
            .select("*")
            .eq("client_id", str(client_id))
            .eq("user_id", str(self.user_id))
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        goals = goals_response.data if goals_response.data else []

        # Get recent touchpoints
        touchpoints_response = (
            supabase.table("touchpoints")
            .select("*")
            .eq("client_id", str(client_id))
            .eq("user_id", str(self.user_id))
            .order("scheduled_date", desc=True)
            .limit(10)
            .execute()
        )
        touchpoints = touchpoints_response.data if touchpoints_response.data else []

        # Get open opportunities
        opportunities_response = (
            supabase.table("business_opportunities")
            .select("*")
            .eq("client_id", str(client_id))
            .eq("user_id", str(self.user_id))
            .eq("outcome", "open")
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )
        opportunities = (
            opportunities_response.data if opportunities_response.data else []
        )

        # Get pending tasks
        tasks_response = (
            supabase.table("tasks")
            .select("*")
            .eq("client_id", str(client_id))
            .eq("user_id", str(self.user_id))
            .eq("status", "pending")
            .order("due_date", desc=False)
            .limit(10)
            .execute()
        )
        tasks = tasks_response.data if tasks_response.data else []

        # Calculate stats
        stats = {
            "total_goals": len(goals),
            "total_touchpoints": len(touchpoints),
            "open_opportunities": len(opportunities),
            "pending_tasks": len(tasks),
            "aum": client.get("total_aum", 0),
            "sip": client.get("sip", 0),
        }

        return {
            "client": client,
            "goals": goals,
            "recent_touchpoints": touchpoints,
            "open_opportunities": opportunities,
            "pending_tasks": tasks,
            "stats": stats,
        }

    async def check_duplicate(self, phone: str) -> Dict[str, Any]:
        """Check if phone number already exists."""
        response = (
            supabase.table("clients")
            .select("id, name, phone")
            .eq("user_id", str(self.user_id))
            .eq("phone", phone)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return {
                "is_duplicate": True,
                "existing_client": response.data[0],
            }
        return {"is_duplicate": False, "existing_client": None}

    async def convert_from_lead(
        self,
        lead_id: UUID,
        birthdate: date,
        email: Optional[str] = None,
        address: Optional[str] = None,
        risk_profile: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convert lead to client."""
        # Get lead data
        lead_response = (
            supabase.table("leads")
            .select("*")
            .eq("id", str(lead_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not lead_response.data:
            raise ValueError("Lead not found")

        lead = lead_response.data[0]

        # Check if already converted
        if lead.get("converted_to_client_id"):
            raise ValueError("Lead already converted to client")

        # Calculate age and age_group
        age = self._calculate_age(birthdate)
        age_group = self._calculate_age_group(age)

        # Calculate TAT days
        lead_created = datetime.fromisoformat(lead["created_at"].replace("Z", "+00:00"))
        tat_days = (datetime.utcnow() - lead_created.replace(tzinfo=None)).days

        # Create client from lead
        client_data = {
            "user_id": str(self.user_id),
            "name": lead["name"],
            "phone": lead["phone"],
            "email": email or lead.get("email"),
            "address": address,
            "area": lead.get("area"),
            "birthdate": birthdate.isoformat(),
            "age": age,
            "age_group": age_group.value if age_group else None,
            "gender": lead.get("gender") or "other",
            "marital_status": lead.get("marital_status"),
            "occupation": lead.get("occupation"),
            "income_group": lead.get("income_group"),
            "risk_profile": risk_profile or lead.get("risk_profile"),
            "source": lead.get("source"),
            "sourced_by": lead.get("sourced_by"),
            "converted_from_lead_id": str(lead_id),
            "conversion_date": date.today().isoformat(),
            "tat_days": tat_days,
        }

        # Insert client
        client_response = supabase.table("clients").insert(client_data).execute()
        if not client_response.data:
            raise Exception("Failed to create client from lead")

        client = client_response.data[0]
        client_id = client["id"]

        # Update lead status
        supabase.table("leads").update(
            {
                "status": "converted",
                "converted_to_client_id": client_id,
                "conversion_date": datetime.utcnow().isoformat(),
                "tat_days": tat_days,
            }
        ).eq("id", str(lead_id)).execute()

        return client

    async def get_cash_flow(self, client_id: UUID) -> Optional[Dict[str, Any]]:
        """Get client cash flow data."""
        response = (
            supabase.table("client_cash_flow")
            .select("*")
            .eq("client_id", str(client_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    async def update_cash_flow(
        self, client_id: UUID, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update client cash flow data."""
        # Verify client exists
        client = await self.get_client(client_id)
        if not client:
            raise ValueError("Client not found")

        # Prepare update data
        update_data = {
            "user_id": str(self.user_id),
            "client_id": str(client_id),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Add provided fields
        if "insurance_premiums" in data:
            update_data["insurance_premiums"] = data["insurance_premiums"]
        if "savings" in data:
            update_data["savings"] = data["savings"]
        if "loans" in data:
            update_data["loans"] = data["loans"]
        if "expenses" in data:
            update_data["expenses"] = data["expenses"]
        if "income" in data:
            update_data["income"] = data["income"]
        if "current_investments" in data:
            update_data["current_investments"] = data["current_investments"]

        # Try to update first, if not exists, insert
        existing = await self.get_cash_flow(client_id)
        if existing:
            response = (
                supabase.table("client_cash_flow")
                .update(update_data)
                .eq("client_id", str(client_id))
                .execute()
            )
        else:
            update_data["created_at"] = datetime.utcnow().isoformat()
            response = supabase.table("client_cash_flow").insert(update_data).execute()

        if response.data:
            return response.data[0]
        raise Exception("Failed to update cash flow")
