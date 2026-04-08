"""Service for WhatsApp form webhook operations.

Resolves MFD phone → user_id, then delegates to existing services.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase_admin
from app.models.lead import LeadCreate
from app.models.task import TaskCreate
from app.models.touchpoint import TouchpointCreate
from app.models.business_opportunity import BOCreate
from app.models.whatsapp_forms import (
    WABOCreate,
    WALeadCreate,
    WASearchResult,
    WATaskCreate,
    WATouchpointCreate,
)
from app.services.bo_service import BOService
from app.services.lead_service import LeadService
from app.services.task_service import TaskService
from app.services.touchpoint_service import TouchpointService

logger = logging.getLogger(__name__)


class WhatsAppFormService:
    """Handles WhatsApp form submissions by resolving phone → user and delegating."""

    async def resolve_user_id(self, mfd_phone: str) -> UUID:
        """Look up user_id from mfd_profiles using 10-digit phone number.

        Searches both +91XXXXXXXXXX and XXXXXXXXXX formats to handle
        inconsistent phone storage in DB.
        """
        phone_with_prefix = f"+91{mfd_phone}"

        response = (
            supabase_admin.table("mfd_profiles")
            .select("user_id")
            .or_(f"phone.eq.{phone_with_prefix},phone.eq.{mfd_phone}")
            .limit(1)
            .execute()
        )

        if not response.data:
            raise ValueError(f"No MFD found with phone number {mfd_phone}")

        return UUID(response.data[0]["user_id"])

    # ──────────────────────────────────────────────
    # Create Lead
    # ──────────────────────────────────────────────

    async def create_lead(self, data: WALeadCreate) -> Dict[str, Any]:
        """Create a lead from WhatsApp form data."""
        user_id = await self.resolve_user_id(data.mfd_phone)

        # Build LeadCreate from provided fields, normalizing phone to +91 format
        lead_data = data.model_dump(exclude={"mfd_phone"}, exclude_unset=True)

        # Normalize lead's phone number to +91 format
        if lead_data.get("phone"):
            lead_data["phone"] = f"+91{lead_data['phone']}"

        # Set defaults for fields the existing service expects
        if "status" not in lead_data:
            lead_data["status"] = "follow_up"

        lead_create = LeadCreate(**lead_data)
        service = LeadService(user_id)
        return await service.create_lead(lead_create)

    # ──────────────────────────────────────────────
    # Create Task
    # ──────────────────────────────────────────────

    async def create_task(self, data: WATaskCreate) -> Dict[str, Any]:
        """Create a task from WhatsApp form data."""
        user_id = await self.resolve_user_id(data.mfd_phone)

        task_data = data.model_dump(exclude={"mfd_phone"}, exclude_unset=True)

        # Set defaults for fields the existing service expects
        if "priority" not in task_data:
            task_data["priority"] = "medium"

        task_create = TaskCreate(**task_data)
        service = TaskService(user_id)
        return await service.create_task(task_create)

    # ──────────────────────────────────────────────
    # Create Touchpoint
    # ──────────────────────────────────────────────

    async def create_touchpoint(self, data: WATouchpointCreate) -> Dict[str, Any]:
        """Create a touchpoint from WhatsApp form data."""
        user_id = await self.resolve_user_id(data.mfd_phone)

        tp_data = data.model_dump(exclude={"mfd_phone"}, exclude_unset=True)

        # Set default status
        if "status" not in tp_data:
            tp_data["status"] = "scheduled"

        tp_create = TouchpointCreate(**tp_data)
        service = TouchpointService(user_id)
        return await service.create_touchpoint(tp_create)

    # ──────────────────────────────────────────────
    # Create Business Opportunity
    # ──────────────────────────────────────────────

    async def create_business_opportunity(self, data: WABOCreate) -> Dict[str, Any]:
        """Create a business opportunity from WhatsApp form data."""
        user_id = await self.resolve_user_id(data.mfd_phone)

        bo_data = data.model_dump(exclude={"mfd_phone"}, exclude_unset=True)

        # Set defaults
        if "opportunity_stage" not in bo_data:
            bo_data["opportunity_stage"] = "identified"

        bo_create = BOCreate(**bo_data)
        service = BOService(user_id)
        return await service.create_opportunity(bo_create)

    # ──────────────────────────────────────────────
    # Search clients / leads
    # ──────────────────────────────────────────────

    async def search_entities(
        self, mfd_phone: str, entity_type: str, query: str
    ) -> List[WASearchResult]:
        """Search clients or leads for the given MFD."""
        user_id = await self.resolve_user_id(mfd_phone)

        table = "clients" if entity_type == "client" else "leads"

        response = (
            supabase_admin.table(table)
            .select("id, name")
            .eq("user_id", str(user_id))
            .ilike("name", f"%{query}%")
            .limit(10)
            .execute()
        )

        results = []
        for row in response.data or []:
            results.append(
                WASearchResult(id=str(row["id"]), name=row.get("name", ""))
            )

        return results
