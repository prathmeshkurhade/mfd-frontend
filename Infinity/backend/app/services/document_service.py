"""Document Service for file management."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import UploadFile

from app.database import supabase
from app.models.common import SuccessMessage
from app.models.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentShareRequest,
    DocumentShareResponse,
    DocumentUpload,
)


class DocumentService:
    """Service for managing documents."""

    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_documents(
        self, client_id: UUID, document_type: Optional[str] = None
    ) -> DocumentListResponse:
        """List documents for a client."""
        query = (
            supabase.table("documents")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("client_id", str(client_id))
        )

        # NOTE: Database schema doesn't have is_deleted column for documents
        # If soft delete is needed, schema must be updated
        # query = query.eq("is_deleted", False)

        if document_type:
            query = query.eq("document_type", document_type)

        response = query.order("created_at", desc=True).execute()

        documents = [DocumentResponse(**doc) for doc in response.data] if response.data else []

        return DocumentListResponse(documents=documents, total=len(documents))

    async def upload_document(
        self, file: UploadFile, data: DocumentUpload
    ) -> DocumentResponse:
        """
        Upload document to storage and save metadata.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - Supabase Storage integration for file upload
        - Google Drive API integration (if user has Google connected)
        - File validation (size, type, virus scanning)
        - Proper error handling for storage failures
        """
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        mime_type = file.content_type or "application/octet-stream"

        # TODO: Upload to Supabase Storage
        # bucket = supabase.storage.from_("documents")
        # file_path = f"{self.user_id}/{data.client_id}/{file.filename}"
        # bucket.upload(file_path, file_content)
        # file_url = bucket.get_public_url(file_path)

        # STUB: Placeholder file URL
        file_url = f"https://storage.supabase.co/documents/{self.user_id}/{data.client_id}/{file.filename}"

        # TODO: Upload to Google Drive if user has Google connected
        drive_file_id = None
        # Check if user has Google connected
        # If yes, upload to Drive and get drive_file_id

        # Save document metadata to database
        document_data = {
            "user_id": str(self.user_id),
            "client_id": str(data.client_id),
            "name": data.name,
            "document_type": data.document_type,
            "file_url": file_url,
            "drive_file_id": drive_file_id,
            "file_size": file_size,
            "mime_type": mime_type,
            "related_entity_type": data.related_entity_type,
            "related_entity_id": str(data.related_entity_id)
            if data.related_entity_id
            else None,
        }

        response = supabase.table("documents").insert(document_data).execute()

        if not response.data:
            raise Exception("Failed to save document metadata")

        return DocumentResponse(**response.data[0])

    async def get_document(self, document_id: UUID) -> Optional[DocumentResponse]:
        """Get document by ID."""
        response = (
            supabase.table("documents")
            .select("*")
            .eq("id", str(document_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )

        if not response.data:
            return None

        return DocumentResponse(**response.data[0])

    async def delete_document(self, document_id: UUID) -> SuccessMessage:
        """
        Delete document.
        
        NOTE: Database schema doesn't have is_deleted column for documents.
        Implementing hard delete. If soft delete is needed, schema must be updated.
        """
        # Get document first to check ownership
        document = await self.get_document(document_id)
        if not document:
            raise ValueError("Document not found")

        # Hard delete from database
        supabase.table("documents").delete().eq("id", str(document_id)).eq(
            "user_id", str(self.user_id)
        ).execute()

        # TODO: Delete from Supabase Storage
        # bucket = supabase.storage.from_("documents")
        # bucket.remove([file_path])

        # TODO: Delete from Google Drive if drive_file_id exists

        return SuccessMessage(message="Document deleted successfully")

    async def share_document(
        self, document_id: UUID, data: DocumentShareRequest
    ) -> DocumentShareResponse:
        """
        Share document with client.
        
        NOTE: This is a STUB implementation. Full implementation requires:
        - WhatsApp Business API integration
        - Email service integration (SendGrid, etc.)
        - Communication log creation
        """
        # Get document
        document = await self.get_document(document_id)
        if not document:
            raise ValueError("Document not found")

        # Update document with sharing details
        shared_at = datetime.now()
        update_data = {
            "shared_with_client": True,
            "shared_at": shared_at.isoformat(),
            "shared_via": data.share_via,
        }

        supabase.table("documents").update(update_data).eq(
            "id", str(document_id)
        ).execute()

        # TODO: Actual sending logic
        # if data.share_via == "whatsapp":
        #     # Send via WhatsApp Business API
        #     pass
        # elif data.share_via == "email":
        #     # Send via email service
        #     pass

        # TODO: Log to communication_logs table
        # communication_log = {
        #     "user_id": str(self.user_id),
        #     "client_id": str(document.client_id),
        #     "type": "document_share",
        #     "channel": data.share_via,
        #     "message": data.message,
        #     "status": "sent",
        # }
        # supabase.table("communication_logs").insert(communication_log).execute()

        return DocumentShareResponse(
            message=f"Document shared via {data.share_via}",
            shared_at=shared_at,
        )

    async def get_client_documents(self, client_id: UUID) -> DocumentListResponse:
        """Get all documents for a specific client."""
        return await self.list_documents(client_id=client_id, document_type=None)
