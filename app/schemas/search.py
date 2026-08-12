import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

class SearchType(str, Enum):
    task = "task"
    project = "project"
    comment = "comment"

class SearchResultItem(BaseModel):
    id: uuid.UUID
    type: SearchType
    title: str
    snippet: str
    rank: float
    created_at: datetime
    project_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total: int
    page: int
    size: int
