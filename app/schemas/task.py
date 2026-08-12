import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="todo", max_length=20)
    priority: str = Field(default="medium", max_length=20)
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    parent_task_id: uuid.UUID | None = None
    position: int = Field(default=0)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(None, max_length=20)
    priority: str | None = Field(None, max_length=20)
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    parent_task_id: uuid.UUID | None = None
    position: int | None = None


class TaskResponse(TaskBase):
    id: uuid.UUID
    project_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
