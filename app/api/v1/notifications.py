import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_notification_service
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.notification import (
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification import NotificationService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    is_read: bool | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """List current user's notifications."""
    items, total = await service.list_notifications(current_user, page, size, is_read)
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get the number of unread notifications for the current user."""
    count = await service.get_unread_count(current_user)
    return UnreadCountResponse(count=count)


@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_as_read(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark a specific notification as read."""
    return await service.mark_as_read(id, current_user)


@router.post("/read-all", response_model=dict)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read for the current user."""
    count = await service.mark_all_as_read(current_user)
    return {"status": "success", "marked_read": count}


@router.delete("/{id}", status_code=204)
async def delete_notification(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Delete a notification."""
    await service.delete_notification(id, current_user)
