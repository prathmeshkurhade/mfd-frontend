"""Message Template Service for managing communication templates."""

from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase
from app.models.common import SuccessMessage
from app.models.message_template import (
    MessageTemplateCreate,
    MessageTemplateListResponse,
    MessageTemplateResponse,
    MessageTemplateUpdate,
)


class TemplateService:
    """Service for managing message templates."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_templates(
        self, template_type: Optional[str] = None, channel: Optional[str] = None
    ) -> MessageTemplateListResponse:
        """List templates (system + user's custom templates)."""
        # Get system templates and user's templates
        query = (
            supabase.table("message_templates")
            .select("*")
            .or_(f"user_id.is.null,user_id.eq.{str(self.user_id)}")
        )

        if template_type:
            query = query.eq("template_type", template_type)

        if channel:
            query = query.eq("channel", channel)

        response = query.order("is_system", desc=True).order("name").execute()

        templates = (
            [MessageTemplateResponse(**tmpl) for tmpl in response.data]
            if response.data
            else []
        )

        return MessageTemplateListResponse(templates=templates, total=len(templates))

    async def get_template(self, template_id: UUID) -> Optional[MessageTemplateResponse]:
        """Get a specific template."""
        response = (
            supabase.table("message_templates")
            .select("*")
            .eq("id", str(template_id))
            .or_(f"user_id.is.null,user_id.eq.{str(self.user_id)}")
            .execute()
        )

        if not response.data:
            return None

        return MessageTemplateResponse(**response.data[0])

    async def create_template(
        self, data: MessageTemplateCreate
    ) -> MessageTemplateResponse:
        """Create a new custom template."""
        template_data = {
            "user_id": str(self.user_id),
            **data.model_dump(mode="json", exclude_unset=True),
            "is_system": False,
            "is_active": True,
        }

        response = supabase.table("message_templates").insert(template_data).execute()

        if not response.data:
            raise Exception("Failed to create template")

        return MessageTemplateResponse(**response.data[0])

    async def update_template(
        self, template_id: UUID, data: MessageTemplateUpdate
    ) -> MessageTemplateResponse:
        """Update a custom template (not system templates)."""
        # Check if template belongs to user and is not system
        existing = await self.get_template(template_id)
        if not existing:
            raise ValueError("Template not found")

        if existing.is_system:
            raise ValueError("Cannot update system templates")

        if existing.user_id != self.user_id:
            raise ValueError("Cannot update another user's template")

        update_data = data.model_dump(mode="json", exclude_unset=True)

        if not update_data:
            raise ValueError("No fields to update")

        response = (
            supabase.table("message_templates")
            .update(update_data)
            .eq("id", str(template_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            raise ValueError("Failed to update template")

        return MessageTemplateResponse(**response.data[0])

    async def delete_template(self, template_id: UUID) -> SuccessMessage:
        """Delete a custom template (not system templates)."""
        # Check if template belongs to user and is not system
        existing = await self.get_template(template_id)
        if not existing:
            raise ValueError("Template not found")

        if existing.is_system:
            raise ValueError("Cannot delete system templates")

        if existing.user_id != self.user_id:
            raise ValueError("Cannot delete another user's template")

        supabase.table("message_templates").delete().eq(
            "id", str(template_id)
        ).eq("user_id", str(self.user_id)).execute()

        return SuccessMessage(message="Template deleted successfully")

    def render_template(
        self, template: MessageTemplateResponse, variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Render template with variables."""
        # Replace placeholders in content
        rendered_content = template.content
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered_content = rendered_content.replace(placeholder, str(value))

        # Replace in subject if present
        rendered_subject = None
        if template.subject:
            rendered_subject = template.subject
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                rendered_subject = rendered_subject.replace(placeholder, str(value))

        return {
            "rendered_content": rendered_content,
            "rendered_subject": rendered_subject,
        }

    async def get_template_by_type(
        self, template_type: str, channel: str
    ) -> Optional[MessageTemplateResponse]:
        """Get template by type and channel (user's custom first, then system)."""
        # Try to get user's custom template first
        user_template_response = (
            supabase.table("message_templates")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("template_type", template_type)
            .eq("channel", channel)
            .eq("is_active", True)
            .execute()
        )

        if user_template_response.data:
            return MessageTemplateResponse(**user_template_response.data[0])

        # Fall back to system template
        system_template_response = (
            supabase.table("message_templates")
            .select("*")
            .is_("user_id", "null")
            .eq("template_type", template_type)
            .eq("channel", channel)
            .eq("is_active", True)
            .execute()
        )

        if system_template_response.data:
            return MessageTemplateResponse(**system_template_response.data[0])

        return None
