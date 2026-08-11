import uuid
from typing import Sequence

from fastapi import HTTPException, status

from app.core.roles import Permission, ProjectRole, project_role_has_permission
from app.models.task import Task
from app.models.user import User
from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository, ProjectMemberRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.task import TaskCreate, TaskUpdate

class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        member_repo: ProjectMemberRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.member_repo = member_repo
        self.audit_repo = audit_repo

    async def _check_permission(
        self, project_id: uuid.UUID, current_user: User, permission: Permission
    ) -> str:
        if current_user.is_superuser:
            return ProjectRole.MANAGER.value

        role = await self.member_repo.get_user_role(project_id, current_user.id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project.",
            )

        if not project_role_has_permission(ProjectRole(role), permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: '{permission.value}'.",
            )
        return role

    async def create_task(
        self, project_id: uuid.UUID, data: TaskCreate, current_user: User
    ) -> Task:
        await self._check_permission(project_id, current_user, Permission.TASK_CREATE)
        
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        if project.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot create tasks in archived projects")

        if data.assignee_id:
            role = await self.member_repo.get_user_role(project_id, data.assignee_id)
            if not role:
                raise HTTPException(status_code=400, detail="Assignee must be a project member")

        task = await self.task_repo.create(
            project_id=project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            creator_id=current_user.id,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            parent_task_id=data.parent_task_id,
            position=data.position,
        )
        
        # Serialize changes for JSONB manually instead of relying on model_dump directly for UUIDs/dates
        changes = {
            "title": data.title,
            "description": data.description,
            "status": data.status,
            "priority": data.priority,
            "assignee_id": str(data.assignee_id) if data.assignee_id else None,
            "due_date": data.due_date.isoformat() if data.due_date else None,
            "parent_task_id": str(data.parent_task_id) if data.parent_task_id else None,
            "position": data.position,
        }
        
        await self.audit_repo.log_action(
            organization_id=project.organization_id,  # type: ignore
            entity_type="task",
            entity_id=task.id,
            action="created",
            actor_id=current_user.id,
            changes=changes,
        )
        return task

    async def get_task(
        self, task_id: uuid.UUID, current_user: User
    ) -> Task:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        await self._check_permission(task.project_id, current_user, Permission.TASK_READ)
        return task

    async def update_task(
        self, task_id: uuid.UUID, data: TaskUpdate, current_user: User
    ) -> Task:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        role = await self._check_permission(task.project_id, current_user, Permission.TASK_READ)
        
        if not current_user.is_superuser:
            if not project_role_has_permission(ProjectRole(role), Permission.TASK_UPDATE_ANY):
                if not project_role_has_permission(ProjectRole(role), Permission.TASK_UPDATE_OWN) or task.creator_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You can only edit your own tasks."
                    )
        
        if data.assignee_id:
            assignee_role = await self.member_repo.get_user_role(task.project_id, data.assignee_id)
            if not assignee_role:
                raise HTTPException(status_code=400, detail="Assignee must be a project member")

        # Track changes
        changes = {}
        for key, value in data.model_dump(exclude_unset=True).items():
            old_value = getattr(task, key)
            if old_value != value:
                old_val_str = str(old_value) if isinstance(old_value, uuid.UUID) else (old_value.isoformat() if hasattr(old_value, "isoformat") else old_value)
                new_val_str = str(value) if isinstance(value, uuid.UUID) else (value.isoformat() if hasattr(value, "isoformat") else value)
                changes[key] = {"old": old_val_str, "new": new_val_str}

        updated_task = await self.task_repo.update(task, **data.model_dump(exclude_unset=True))
        
        if changes:
            project = await self.project_repo.get_by_id(task.project_id)
            await self.audit_repo.log_action(
                organization_id=project.organization_id,  # type: ignore
                entity_type="task",
                entity_id=task.id,
                action="updated",
                actor_id=current_user.id,
                changes=changes,
            )

        return updated_task

    async def delete_task(
        self, task_id: uuid.UUID, current_user: User
    ) -> None:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await self._check_permission(task.project_id, current_user, Permission.TASK_DELETE)
        
        project = await self.project_repo.get_by_id(task.project_id)
        await self.audit_repo.log_action(
            organization_id=project.organization_id,  # type: ignore
            entity_type="task",
            entity_id=task.id,
            action="deleted",
            actor_id=current_user.id,
            changes=None,
        )

        await self.task_repo.delete(task)
