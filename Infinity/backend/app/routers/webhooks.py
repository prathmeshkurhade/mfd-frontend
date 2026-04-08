from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.models.webhook import DeliveryStatusPayload, WebhookPayload, WhatsAppMessagePayload
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# Dependency for API key validation
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


class WebhookStatusResponse(BaseModel):
    status: str


class WhatsAppMessageResponse(BaseModel):
    status: str
    input_id: str


@router.post("/whatsapp/delivery-status", response_model=WebhookStatusResponse)
async def handle_whatsapp_delivery(
    payload: DeliveryStatusPayload,
    _: None = Depends(verify_webhook_api_key),
):
    """Handle WhatsApp delivery status webhook."""
    service = WebhookService()
    try:
        # Log webhook
        webhook_payload = WebhookPayload(
            source="whatsapp_notif",
            event_type="delivery_status",
            payload=payload.model_dump(mode="json"),
        )
        webhook_log = await service.log_webhook(webhook_payload)

        # Process delivery status
        await service.process_delivery_status(payload)

        # Mark webhook as processed
        await service.mark_webhook_processed(
            webhook_log.id,
            {"status": "processed", "message": "Delivery status updated"},
        )

        return WebhookStatusResponse(status="ok")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )


@router.post("/whatsapp/message", response_model=WhatsAppMessageResponse)
async def handle_whatsapp_message(
    payload: WhatsAppMessagePayload,
    _: None = Depends(verify_webhook_api_key),
):
    """Handle incoming WhatsApp message webhook."""
    service = WebhookService()
    try:
        # Log webhook
        webhook_payload = WebhookPayload(
            source="whatsapp_input",
            event_type="message_received",
            payload=payload.model_dump(mode="json"),
        )
        webhook_log = await service.log_webhook(webhook_payload)

        # Process WhatsApp message
        result = await service.process_whatsapp_message(payload)

        # Mark webhook as processed
        await service.mark_webhook_processed(
            webhook_log.id,
            {
                "status": "processed" if result.success else "failed",
                "input_id": str(result.input_id),
                "message": result.message,
            },
        )

        return WhatsAppMessageResponse(
            status="received",
            input_id=str(result.input_id),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )


@router.post("/email/delivery-status", response_model=WebhookStatusResponse)
async def handle_email_delivery(
    payload: DeliveryStatusPayload,
    _: None = Depends(verify_webhook_api_key),
):
    """Handle email delivery status webhook."""
    service = WebhookService()
    try:
        # Log webhook
        webhook_payload = WebhookPayload(
            source="email_service",
            event_type="delivery_status",
            payload=payload.model_dump(mode="json"),
        )
        webhook_log = await service.log_webhook(webhook_payload)

        # Process delivery status (same logic as WhatsApp)
        await service.process_delivery_status(payload)

        # Mark webhook as processed
        await service.mark_webhook_processed(
            webhook_log.id,
            {"status": "processed", "message": "Delivery status updated"},
        )

        return WebhookStatusResponse(status="ok")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        )
