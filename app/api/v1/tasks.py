import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.database import get_db
from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository, ProjectMemberRepository
from app.repositories.comment import CommentRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.notification import NotificationRepository
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskResponse, TaskUpdate
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.audit_log import AuditLogResponse
from app.services.task import TaskService
from app.services.comment import CommentService


def get_task_service(
    db: AsyncSession = Depends(get_db),
) -> TaskService:
    return TaskService(
        task_repo=TaskRepository(db),
        project_repo=ProjectRepository(db),
        member_repo=ProjectMemberRepository(db),
        audit_repo=AuditLogRepository(db),
        notification_repo=NotificationRepository(db),
    )

def get_comment_service(
    db: AsyncSession = Depends(get_db),
) -> CommentService:
    return CommentService(
        comment_repo=CommentRepository(db),
        task_repo=TaskRepository(db),
        project_repo=ProjectRepository(db),
        member_repo=ProjectMemberRepository(db),
        audit_repo=AuditLogRepository(db),
        notification_repo=NotificationRepository(db),
    )


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    dependencies=[Depends(get_current_user)],
)

@router.get(
    "/my",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks assigned to me",
)
async def list_my_tasks(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> PaginatedResponse[TaskResponse]:
    offset = (page - 1) * size
    tasks, total = await service.task_repo.list_my_tasks(current_user.id, offset, size)
    return PaginatedResponse[TaskResponse].create(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        size=size,
    )

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
)
async def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(task_id, current_user)
    return TaskResponse.model_validate(task)

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: CurrentUser,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.update_task(task_id, data, current_user)
    return TaskResponse.model_validate(task)

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
)
async def delete_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete_task(task_id, current_user)

@router.get(
    "/{task_id}/history",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Get task history",
)
async def get_task_history(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> PaginatedResponse[AuditLogResponse]:
    # Ensure user has access
    await service.get_task(task_id, current_user)
    
    offset = (page - 1) * size
    logs, total = await service.audit_repo.get_history("task", task_id, offset, size)
    return PaginatedResponse[AuditLogResponse].create(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )

# ── Comments ─────────────────────────────────────────────────────────────

@router.post(
    "/{task_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a comment to a task",
)
async def create_comment(
    task_id: uuid.UUID,
    data: CommentCreate,
    current_user: CurrentUser,
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    comment = await service.create_comment(task_id, data, current_user)
    return CommentResponse.model_validate(comment)

@router.get(
    "/{task_id}/comments",
    response_model=PaginatedResponse[CommentResponse],
    summary="List task comments",
)
async def list_task_comments(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: CommentService = Depends(get_comment_service),
) -> PaginatedResponse[CommentResponse]:
    comments, total = await service.list_comments(task_id, current_user, page, size)
    return PaginatedResponse[CommentResponse].create(
        items=[CommentResponse.model_validate(c) for c in comments],
        total=total,
        page=page,
        size=size,
    )
