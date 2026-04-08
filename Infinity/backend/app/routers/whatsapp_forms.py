"""WhatsApp form webhook endpoints.

These endpoints allow the WhatsApp bot to create leads, tasks,
touchpoints, and business opportunities on behalf of MFDs.

Auth: X-API-Key header (same key as other webhooks).
User identification: mfd_phone (10-digit number) in request body.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import settings
from app.models.whatsapp_forms import (
    WABOCreate,
    WAFormResponse,
    WALeadCreate,
    WASearchRequest,
    WASearchResponse,
    WATaskCreate,
    WATouchpointCreate,
)
from app.services.whatsapp_form_service import WhatsAppFormService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp-forms", tags=["WhatsApp Forms"])


# ──────────────────────────────────────────────
# API Key dependency (same pattern as webhooks.py)
# ──────────────────────────────────────────────

def verify_webhook_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify webhook API key from header."""
    webhook_api_key = getattr(settings, "WEBHOOK_API_KEY", "")

    if not webhook_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook API key not configured",
        )

    if x_api_key != webhook_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


# ──────────────────────────────────────────────
# Create Lead
# ──────────────────────────────────────────────

@router.post("/create-lead", response_model=WAFormResponse)
async def wa_create_lead(
    data: WALeadCreate,
    _: None = Depends(verify_webhook_api_key),
):
    """Create a lead from WhatsApp form submission."""
    service = WhatsAppFormService()
    try:
        result = await service.create_lead(data)
        return WAFormResponse(
            status="success",
            message="Lead created successfully",
            entity_id=str(result.get("id", "")),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp create lead failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────
# Create Task
# ──────────────────────────────────────────────

@router.post("/create-task", response_model=WAFormResponse)
async def wa_create_task(
    data: WATaskCreate,
    _: None = Depends(verify_webhook_api_key),
):
    """Create a task from WhatsApp form submission."""
    service = WhatsAppFormService()
    try:
        result = await service.create_task(data)
        return WAFormResponse(
            status="success",
            message="Task created successfully",
            entity_id=str(result.get("id", "")),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp create task failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────
# Create Touchpoint (Meeting)
# ──────────────────────────────────────────────

@router.post("/create-touchpoint", response_model=WAFormResponse)
async def wa_create_touchpoint(
    data: WATouchpointCreate,
    _: None = Depends(verify_webhook_api_key),
):
    """Create a touchpoint/meeting from WhatsApp form submission."""
    service = WhatsAppFormService()
    try:
        result = await service.create_touchpoint(data)
        return WAFormResponse(
            status="success",
            message="Touchpoint created successfully",
            entity_id=str(result.get("id", "")),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp create touchpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────
# Create Business Opportunity
# ──────────────────────────────────────────────

@router.post("/create-business-opportunity", response_model=WAFormResponse)
async def wa_create_business_opportunity(
    data: WABOCreate,
    _: None = Depends(verify_webhook_api_key),
):
    """Create a business opportunity from WhatsApp form submission."""
    service = WhatsAppFormService()
    try:
        result = await service.create_business_opportunity(data)
        return WAFormResponse(
            status="success",
            message="Business opportunity created successfully",
            entity_id=str(result.get("id", "")),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp create business opportunity failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ──────────────────────────────────────────────
# Search clients / leads
# ──────────────────────────────────────────────

@router.post("/search", response_model=WASearchResponse)
async def wa_search(
    data: WASearchRequest,
    _: None = Depends(verify_webhook_api_key),
):
    """Search clients or leads for client/lead linking in forms."""
    service = WhatsAppFormService()
    try:
        results = await service.search_entities(
            mfd_phone=data.mfd_phone,
            entity_type=data.entity_type,
            query=data.query,
        )
        return WASearchResponse(results=results, total=len(results))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"WhatsApp search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
