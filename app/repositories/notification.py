import uuid
from typing import Sequence
from datetime import datetime, timezone

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        type: str,
        title: str,
        message: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            type=type,
            title=title,
            message=message,
            data=data,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_for_user(
        self, user_id: uuid.UUID, offset: int = 0, limit: int = 50, is_read: bool | None = None
    ) -> tuple[Sequence[Notification], int]:
        # Build base query
        stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)

        # Apply filters
        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
            count_stmt = count_stmt.where(Notification.is_read == is_read)

        # Count total
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Get paginated results
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def count_unread_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def update(self, notification: Notification, **kwargs) -> Notification:
        for key, value in kwargs.items():
            setattr(notification, key, value)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def delete(self, notification: Notification) -> None:
        await self.session.delete(notification)
        await self.session.commit()
