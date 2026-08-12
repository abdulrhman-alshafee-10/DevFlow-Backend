from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TaskAnalyzeRequest(BaseModel):
    focus: Optional[str] = Field(None, description="Specific area to focus the analysis on (e.g., 'risks', 'timeline')")

class ProjectSummarizeRequest(BaseModel):
    pass # Currently empty, but allows future expansion

class TaskSuggestSubtasksRequest(BaseModel):
    pass

class TaskSuggestSubtasksResponse(BaseModel):
    subtasks: list[str]

class AIChatRequest(BaseModel):
    message: str = Field(..., description="The message to send to the AI")
    project_id: Optional[UUID] = Field(None, description="Optional project context")

class AIUsageResponse(BaseModel):
    id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    endpoint: str
    prompt_tokens: int
    completion_tokens: int
    cost: float
    created_at: datetime

    class Config:
        from_attributes = True
