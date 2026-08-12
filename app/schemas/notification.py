import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=500)
    message: str | None = None
    data: dict[str, Any] | None = None
    is_read: bool = False
    read_at: datetime | None = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID
    organization_id: uuid.UUID


class NotificationUpdate(BaseModel):
    is_read: bool


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    count: int
