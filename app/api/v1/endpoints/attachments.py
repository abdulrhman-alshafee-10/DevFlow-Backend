import uuid
from typing import Sequence

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.task import Task
from app.schemas.attachment import AttachmentResponse, AttachmentURLResponse
from app.services.attachment_service import AttachmentService
from sqlalchemy import select

router = APIRouter()


async def get_task_or_404(task_id: uuid.UUID, session: AsyncSession) -> Task:
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/tasks/{task_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Verify task exists
    await get_task_or_404(task_id, session)

    # TODO: Add authorization check here (e.g., is user a member of the project?)
    # For now, just allow authenticated users.

    service = AttachmentService(session)
    return await service.upload_attachment(task_id, current_user.id, file)


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    # Verify task exists
    await get_task_or_404(task_id, session)

    service = AttachmentService(session)
    return await service.get_task_attachments(task_id)


@router.get("/attachments/{id}/download", response_model=AttachmentURLResponse)
async def get_download_url(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    service = AttachmentService(session)
    attachment = await service.get_attachment_by_id(id)
    
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    url = await service.generate_download_url(attachment)
    return AttachmentURLResponse(url=url, expires_in=900)


@router.delete("/attachments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    service = AttachmentService(session)
    attachment = await service.get_attachment_by_id(id)
    
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    # Authorization: Only uploader or admin can delete
    if attachment.uploader_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You do not have permission to delete this attachment"
        )

    await service.delete_attachment(attachment)
