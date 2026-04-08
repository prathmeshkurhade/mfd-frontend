from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_id
from app.models.whatsapp_input import (
    ProcessInputResponse,
    WhatsAppDataInputListResponse,
    WhatsAppDataInputResponse,
)
from app.services.whatsapp_input_service import WhatsAppInputService

router = APIRouter(prefix="/whatsapp-inputs", tags=["WhatsApp Inputs"])


class TranscriptionUpdate(BaseModel):
    transcription: str


@router.get("/", response_model=WhatsAppDataInputListResponse)
async def list_inputs(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List WhatsApp data inputs."""
    service = WhatsAppInputService(user_id)
    try:
        inputs = await service.list_inputs(status_filter)
        return inputs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inputs: {str(e)}",
        )


@router.get("/{input_id}", response_model=WhatsAppDataInputResponse)
async def get_input(
    input_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific WhatsApp input."""
    service = WhatsAppInputService(user_id)
    try:
        input_record = await service.get_input(input_id)
        if not input_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Input not found",
            )
        return input_record
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get input: {str(e)}",
        )


@router.post("/{input_id}/process", response_model=ProcessInputResponse)
async def process_input(
    input_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Manually trigger processing of WhatsApp input."""
    service = WhatsAppInputService(user_id)
    try:
        result = await service.process_text_input(input_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process input: {str(e)}",
        )


@router.post("/{input_id}/transcription", response_model=ProcessInputResponse)
async def update_transcription(
    input_id: UUID,
    data: TranscriptionUpdate,
    user_id: UUID = Depends(get_current_user_id),
):
    """Update voice note transcription and process it."""
    service = WhatsAppInputService(user_id)
    try:
        # Verify input exists
        input_record = await service.get_input(input_id)
        if not input_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Input not found",
            )

        # Process with transcription
        result = await service.process_voice_input(input_id, data.transcription)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update transcription: {str(e)}",
        )
