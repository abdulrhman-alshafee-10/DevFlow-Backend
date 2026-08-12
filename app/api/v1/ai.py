import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.ai import (
    TaskAnalyzeRequest,
    ProjectSummarizeRequest,
    TaskSuggestSubtasksRequest,
    TaskSuggestSubtasksResponse,
    AIChatRequest,
)
from app.services.ai_service import AIService

router = APIRouter()

def get_ai_service(db: AsyncSession = Depends(get_db)) -> AIService:
    return AIService(db)

async def stream_generator(generator: AsyncGenerator[str, None]):
    try:
        async for chunk in generator:
            yield {"data": chunk}
    except Exception as e:
        yield {"event": "error", "data": str(e)}

@router.post("/tasks/{task_id}/analyze")
async def analyze_task(
    task_id: uuid.UUID,
    request: TaskAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """Stream an AI analysis of a specific task."""
    generator = ai_service.analyze_task(
        user_id=current_user.id,
        task_id=task_id,
        focus=request.focus
    )
    return EventSourceResponse(stream_generator(generator))

@router.post("/tasks/{task_id}/suggest-subtasks", response_model=TaskSuggestSubtasksResponse)
async def suggest_subtasks(
    task_id: uuid.UUID,
    request: TaskSuggestSubtasksRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """Get AI suggestions for subtasks (returns JSON, not streamed)."""
    subtasks = await ai_service.suggest_subtasks(
        user_id=current_user.id,
        task_id=task_id
    )
    return TaskSuggestSubtasksResponse(subtasks=subtasks)

@router.post("/projects/{project_id}/summarize")
async def summarize_project(
    project_id: uuid.UUID,
    request: ProjectSummarizeRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """Stream an AI summary of a project."""
    generator = ai_service.summarize_project(
        user_id=current_user.id,
        project_id=project_id
    )
    return EventSourceResponse(stream_generator(generator))

@router.post("/chat")
async def chat_with_ai(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
):
    """Chat with the AI assistant (streamed)."""
    generator = ai_service.chat(
        user_id=current_user.id,
        message=request.message,
        project_id=request.project_id
    )
    return EventSourceResponse(stream_generator(generator))
