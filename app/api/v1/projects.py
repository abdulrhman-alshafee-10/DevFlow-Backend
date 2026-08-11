"""
app/api/v1/projects.py
───────────────────────
Endpoints for projects and project members.
"""

import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OrgMemberDep, ProjectMemberDep, get_current_user, RequirePermission
from app.core.roles import Permission
from app.database import get_db
from app.repositories.organization import OrganizationMemberRepository
from app.repositories.project import ProjectMemberRepository, ProjectRepository
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdate,
)
from app.schemas.task import TaskCreate, TaskResponse
from app.services.project import ProjectService
from app.api.v1.tasks import get_task_service, TaskService


def get_project_service(
    db: AsyncSession = Depends(get_db),
) -> ProjectService:
    return ProjectService(
        project_repo=ProjectRepository(db),
        member_repo=ProjectMemberRepository(db),
        org_member_repo=OrganizationMemberRepository(db),
    )


org_project_router = APIRouter(
    prefix="/organizations/{org_id}/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)],
)

project_router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(get_current_user)],
)


# ══════════════════════════════════════════════════════════════════════════════
# ORGANIZATION-SCOPED ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@org_project_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project in the organization",
)
async def create_project(
    data: ProjectCreate,
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Create a project within an organization.
    Requires `project:create` permission (ADMIN or OWNER).
    """
    org, org_membership = ctx
    project = await service.create_project(org.id, data, current_user)
    member_count = await service.member_repo.get_member_count(project.id)
    return ProjectResponse(
        **{k: getattr(project, k) for k in project.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        my_role="manager",
        member_count=member_count,
    )


@org_project_router.get(
    "",
    response_model=PaginatedResponse[ProjectSummary],
    summary="List organization projects",
)
async def list_org_projects(
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse[ProjectSummary]:
    """
    List all projects in the organization.
    Requires `org:read` permission (any org member).
    """
    org, _ = ctx
    projects, total = await service.list_org_projects(org.id, current_user, page=page, size=size)
    
    items = []
    for project in projects:
        role = await service.member_repo.get_user_role(project.id, current_user.id)
        items.append(
            ProjectSummary(
                id=project.id,
                name=project.name,
                slug=project.slug,
                status=project.status,
                my_role=role,
            )
        )
        
    return PaginatedResponse[ProjectSummary].create(
        items=items, total=total, page=page, size=size
    )


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT-SCOPED ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@project_router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
)
async def get_project(
    ctx: ProjectMemberDep,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Get full details of a project.
    Caller must be a member of the project.
    """
    project, membership = ctx
    member_count = await service.member_repo.get_member_count(project.id)
    return ProjectResponse(
        **{k: getattr(project, k) for k in project.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        my_role=membership.role,
        member_count=member_count,
    )


@project_router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project details",
)
async def update_project(
    data: ProjectUpdate,
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Update project details.
    Requires `project:update` permission.
    """
    project, membership = ctx
    updated = await service.update_project(project.id, data, current_user)
    member_count = await service.member_repo.get_member_count(project.id)
    return ProjectResponse(
        **{k: getattr(updated, k) for k in updated.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        my_role=membership.role,
        member_count=member_count,
    )


@project_router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
)
async def delete_project(
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """
    Permanently delete a project and all associated tasks.
    Requires `project:delete` permission.
    """
    project, _ = ctx
    await service.delete_project(project.id, current_user)


@project_router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive project",
)
async def archive_project(
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Archive a project.
    Requires `project:update` permission.
    """
    project, membership = ctx
    archived = await service.archive_project(project.id, current_user)
    member_count = await service.member_repo.get_member_count(project.id)
    return ProjectResponse(
        **{k: getattr(archived, k) for k in archived.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        my_role=membership.role,
        member_count=member_count,
    )


@project_router.post(
    "/{project_id}/unarchive",
    response_model=ProjectResponse,
    summary="Unarchive project",
)
async def unarchive_project(
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Unarchive a project.
    Requires `project:update` permission.
    """
    project, membership = ctx
    unarchived = await service.unarchive_project(project.id, current_user)
    member_count = await service.member_repo.get_member_count(project.id)
    return ProjectResponse(
        **{k: getattr(unarchived, k) for k in unarchived.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        my_role=membership.role,
        member_count=member_count,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT MEMBERS
# ══════════════════════════════════════════════════════════════════════════════

@project_router.get(
    "/{project_id}/members",
    response_model=PaginatedResponse[ProjectMemberResponse],
    summary="List project members",
)
async def list_project_members(
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse[ProjectMemberResponse]:
    """
    List members of a project.
    Requires `project:read` permission.
    """
    project, _ = ctx
    members, total = await service.list_members(project.id, current_user, page=page, size=size)
    return PaginatedResponse[ProjectMemberResponse].create(
        items=[ProjectMemberResponse(**m) for m in members],
        total=total,
        page=page,
        size=size,
    )


@project_router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member to the project",
)
async def add_project_member(
    data: ProjectMemberAdd,
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    """
    Add a user to a project.
    Requires `project:members:manage` permission.
    The user must already be a member of the organization.
    """
    project, _ = ctx
    added = await service.add_member(project.id, data.user_id, data.role, current_user)
    
    # Refetch for the response model (joins user data)
    members, _ = await service.member_repo.list_members(project.id, offset=0, limit=1000)
    member_dict = next((m for m in members if m["user_id"] == added.user_id), None)
    if member_dict is None:
        return ProjectMemberResponse(
            user_id=added.user_id,
            email="",
            username="",
            full_name=None,
            avatar_url=None,
            role=added.role,
            added_at=added.added_at,
        )
    return ProjectMemberResponse(**member_dict)


@project_router.patch(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
    summary="Update project member role",
)
async def update_project_member_role(
    user_id: uuid.UUID,
    data: ProjectMemberUpdate,
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectMemberResponse:
    """
    Update the role of a project member.
    Requires `project:members:manage` permission.
    Cannot update your own role.
    """
    project, _ = ctx
    updated = await service.update_member_role(project.id, user_id, data.role, current_user)
    
    # Refetch for the response model
    members, _ = await service.member_repo.list_members(project.id, offset=0, limit=1000)
    member_dict = next((m for m in members if m["user_id"] == updated.user_id), None)
    if member_dict is None:
        return ProjectMemberResponse(
            user_id=updated.user_id,
            email="",
            username="",
            full_name=None,
            avatar_url=None,
            role=updated.role,
            added_at=updated.added_at,
        )
    return ProjectMemberResponse(**member_dict)


@project_router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove project member",
)
async def remove_project_member(
    user_id: uuid.UUID,
    ctx: ProjectMemberDep,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> None:
    """
    Remove a member from the project.
    Requires `project:members:manage` permission.
    """
    project, _ = ctx
    await service.remove_member(project.id, user_id, current_user)

# ══════════════════════════════════════════════════════════════════════════════
# PROJECT TASKS
# ══════════════════════════════════════════════════════════════════════════════

@project_router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(
    project_id: uuid.UUID,
    data: TaskCreate,
    current_user: CurrentUser,
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    """
    Create a new task within a project.
    Requires `task:create` permission.
    """
    task = await service.create_task(project_id, data, current_user)
    return TaskResponse.model_validate(task)


@project_router.get(
    "/{project_id}/tasks",
    response_model=PaginatedResponse[TaskResponse],
    summary="List project tasks",
)
async def list_project_tasks(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: uuid.UUID | None = None,
    search: str | None = None,
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: TaskService = Depends(get_task_service),
) -> PaginatedResponse[TaskResponse]:
    """
    List tasks in a project with filtering, sorting, and pagination.
    Requires `task:read` permission.
    """
    from app.core.roles import Permission
    await service._check_permission(project_id, current_user, Permission.TASK_READ)
    
    offset = (page - 1) * size
    tasks, total = await service.task_repo.list_tasks(
        project_id=project_id,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        offset=offset,
        limit=size,
    )
    return PaginatedResponse[TaskResponse].create(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        size=size,
    )
