import uuid
import magic
from typing import BinaryIO, Sequence

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment
from app.repositories.attachment_repository import AttachmentRepository
from app.utils.storage import storage_client

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
}


class AttachmentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AttachmentRepository(session)

    async def _validate_file(self, file: UploadFile) -> tuple[int, str]:
        # Validate size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {MAX_FILE_SIZE / (1024*1024)}MB."
            )

        # Validate content using python-magic
        file_header = file.file.read(2048)
        file.file.seek(0)
        
        mime_type = magic.from_buffer(file_header, mime=True)
        
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type {mime_type} is not allowed."
            )

        return file_size, mime_type

    async def upload_attachment(self, task_id: uuid.UUID, uploader_id: uuid.UUID, file: UploadFile) -> Attachment:
        file_size, mime_type = await self._validate_file(file)

        # Generate a unique storage key
        storage_key = f"tasks/{task_id}/{uuid.uuid4()}-{file.filename}"

        # Upload to MinIO
        upload_success = await storage_client.upload_file(file.file, storage_key, mime_type)
        if not upload_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage."
            )

        # Create database record
        attachment = Attachment(
            task_id=task_id,
            uploader_id=uploader_id,
            original_filename=file.filename or "unknown",
            storage_key=storage_key,
            file_size=file_size,
            mime_type=mime_type,
        )
        
        return await self.repository.create(attachment)

    async def get_task_attachments(self, task_id: uuid.UUID) -> Sequence[Attachment]:
        return await self.repository.get_by_task_id(task_id)

    async def get_attachment_by_id(self, attachment_id: uuid.UUID) -> Attachment | None:
        return await self.repository.get_by_id(attachment_id)

    async def generate_download_url(self, attachment: Attachment, expires_in: int = 900) -> str:
        url = await storage_client.get_presigned_url(attachment.storage_key, expires_in)
        if not url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL."
            )
        return url

    async def delete_attachment(self, attachment: Attachment) -> None:
        # Delete from MinIO
        delete_success = await storage_client.delete_file(attachment.storage_key)
        if not delete_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file from storage."
            )
            
        # Delete from database
        await self.repository.delete(attachment)
