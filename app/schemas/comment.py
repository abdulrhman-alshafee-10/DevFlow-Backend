import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(CommentBase):
    pass


class CommentResponse(CommentBase):
    id: uuid.UUID
    task_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
