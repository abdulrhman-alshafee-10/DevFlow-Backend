import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentBase(BaseModel):
    task_id: uuid.UUID
    uploader_id: uuid.UUID
    original_filename: str
    file_size: int
    mime_type: str


class AttachmentResponse(AttachmentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttachmentURLResponse(BaseModel):
    url: str
    expires_in: int
