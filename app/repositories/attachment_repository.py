import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attachment import Attachment


class AttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, attachment: Attachment) -> Attachment:
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment

    async def get_by_id(self, attachment_id: uuid.UUID) -> Attachment | None:
        result = await self.session.execute(
            select(Attachment).where(Attachment.id == attachment_id)
        )
        return result.scalars().first()

    async def get_by_task_id(self, task_id: uuid.UUID) -> Sequence[Attachment]:
        result = await self.session.execute(
            select(Attachment)
            .where(Attachment.task_id == task_id)
            .order_by(Attachment.created_at.desc())
        )
        return result.scalars().all()

    async def delete(self, attachment: Attachment) -> None:
        await self.session.delete(attachment)
        await self.session.commit()
