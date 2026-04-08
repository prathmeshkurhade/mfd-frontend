from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.message_template import (
    MessageTemplateCreate,
    MessageTemplateListResponse,
    MessageTemplateResponse,
    MessageTemplateUpdate,
    RenderTemplateRequest,
    RenderTemplateResponse,
)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("/", response_model=MessageTemplateListResponse)
async def list_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List message templates (system + user's custom)."""
    service = TemplateService(user_id)
    try:
        templates = await service.list_templates(template_type, channel)
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}",
        )


@router.post("/", response_model=MessageTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: MessageTemplateCreate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Create a new custom template."""
    service = TemplateService(user_id)
    try:
        template = await service.create_template(data)
        return template
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}",
        )


@router.get("/{template_id}", response_model=MessageTemplateResponse)
async def get_template(
    template_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific template."""
    service = TemplateService(user_id)
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}",
        )


@router.put("/{template_id}", response_model=MessageTemplateResponse)
async def update_template(
    template_id: UUID,
    data: MessageTemplateUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update a custom template."""
    service = TemplateService(user_id)
    try:
        template = await service.update_template(template_id, data)
        return template
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}",
        )


@router.delete("/{template_id}", response_model=SuccessMessage)
async def delete_template(
    template_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete a custom template."""
    service = TemplateService(user_id)
    try:
        result = await service.delete_template(template_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}",
        )


@router.post("/render", response_model=RenderTemplateResponse)
async def render_template(
    data: RenderTemplateRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Render a template with variables."""
    service = TemplateService(user_id)
    try:
        # Get template
        template = await service.get_template(data.template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )

        # Render
        rendered = service.render_template(template, data.variables)

        return RenderTemplateResponse(
            rendered_content=rendered["rendered_content"],
            rendered_subject=rendered["rendered_subject"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render template: {str(e)}",
        )
