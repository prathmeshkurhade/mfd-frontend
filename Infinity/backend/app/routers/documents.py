from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.auth.dependencies import get_current_user_id
from app.models.common import SuccessMessage
from app.models.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentShareRequest,
    DocumentShareResponse,
    DocumentUpload,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    client_id: UUID = Query(..., description="Client ID to filter documents"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    user_id: UUID = Depends(get_current_user_id),
):
    """List documents for a client."""
    service = DocumentService(user_id)
    try:
        result = await service.list_documents(client_id, document_type)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    client_id: UUID = Query(..., description="Client ID"),
    name: str = Query(..., description="Document name"),
    document_type: Optional[str] = Query(None, description="Document type"),
    related_entity_type: Optional[str] = Query(None, description="Related entity type"),
    related_entity_id: Optional[UUID] = Query(None, description="Related entity ID"),
    user_id: UUID = Depends(get_current_user_id),
):
    """Upload a document."""
    service = DocumentService(user_id)
    try:
        # Create DocumentUpload data object
        upload_data = DocumentUpload(
            client_id=client_id,
            name=name,
            document_type=document_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )

        result = await service.upload_document(file, upload_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get a specific document."""
    service = DocumentService(user_id)
    try:
        document = await service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}",
        )


@router.delete("/{document_id}", response_model=SuccessMessage)
async def delete_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Delete a document."""
    service = DocumentService(user_id)
    try:
        result = await service.delete_document(document_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.post("/{document_id}/share", response_model=DocumentShareResponse)
async def share_document(
    document_id: UUID,
    data: DocumentShareRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Share document with client via WhatsApp or email."""
    service = DocumentService(user_id)
    try:
        result = await service.share_document(document_id, data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share document: {str(e)}",
        )


@router.get("/client/{client_id}", response_model=DocumentListResponse)
async def get_client_documents(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Get all documents for a specific client."""
    service = DocumentService(user_id)
    try:
        result = await service.get_client_documents(client_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client documents: {str(e)}",
        )
