import uuid
from typing import Sequence
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, notification_repo: NotificationRepository) -> None:
        self.notification_repo = notification_repo

    async def create_notification(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        type: str,
        title: str,
        message: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        return await self.notification_repo.create(
            user_id=user_id,
            organization_id=organization_id,
            type=type,
            title=title,
            message=message,
            data=data,
        )

    async def list_notifications(
        self, current_user: User, page: int = 1, size: int = 50, is_read: bool | None = None
    ) -> tuple[Sequence[Notification], int]:
        offset = (page - 1) * size
        return await self.notification_repo.list_for_user(
            user_id=current_user.id, offset=offset, limit=size, is_read=is_read
        )

    async def get_unread_count(self, current_user: User) -> int:
        return await self.notification_repo.count_unread_for_user(current_user.id)

    async def mark_as_read(
        self, notification_id: uuid.UUID, current_user: User
    ) -> Notification:
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own notifications",
            )
            
        if not notification.is_read:
            return await self.notification_repo.update(
                notification, is_read=True, read_at=datetime.now(timezone.utc)
            )
        return notification

    async def mark_all_as_read(self, current_user: User) -> int:
        return await self.notification_repo.mark_all_as_read(current_user.id)

    async def delete_notification(
        self, notification_id: uuid.UUID, current_user: User
    ) -> None:
        notification = await self.notification_repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own notifications",
            )
            
        await self.notification_repo.delete(notification)
