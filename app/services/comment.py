import uuid
from typing import Sequence

from fastapi import HTTPException, status

from app.core.roles import Permission, ProjectRole, project_role_has_permission
from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment import CommentRepository
from app.repositories.task import TaskRepository
from app.repositories.project import ProjectRepository, ProjectMemberRepository
from app.repositories.audit_log import AuditLogRepository
from app.schemas.comment import CommentCreate, CommentUpdate

class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
        member_repo: ProjectMemberRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.comment_repo = comment_repo
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

    async def create_comment(
        self, task_id: uuid.UUID, data: CommentCreate, current_user: User
    ) -> Comment:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        await self._check_permission(task.project_id, current_user, Permission.COMMENT_CREATE)
        
        comment = await self.comment_repo.create(
            task_id=task_id,
            author_id=current_user.id,
            content=data.content,
        )
        
        project = await self.project_repo.get_by_id(task.project_id)
        await self.audit_repo.log_action(
            organization_id=project.organization_id,  # type: ignore
            entity_type="comment",
            entity_id=comment.id,
            action="created",
            actor_id=current_user.id,
            changes={"content": data.content},
        )
        return comment

    async def list_comments(
        self, task_id: uuid.UUID, current_user: User, page: int = 1, size: int = 20
    ) -> tuple[Sequence[Comment], int]:
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
            
        await self._check_permission(task.project_id, current_user, Permission.COMMENT_READ)
        
        offset = (page - 1) * size
        return await self.comment_repo.list_comments(task_id, offset, size)

    async def update_comment(
        self, comment_id: uuid.UUID, data: CommentUpdate, current_user: User
    ) -> Comment:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        task = await self.task_repo.get_by_id(comment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        role = await self._check_permission(task.project_id, current_user, Permission.COMMENT_READ)
        
        if not current_user.is_superuser:
            if comment.author_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only edit your own comments."
                )

        old_content = comment.content
        updated_comment = await self.comment_repo.update(comment, **data.model_dump(exclude_unset=True))
        
        if old_content != updated_comment.content:
            project = await self.project_repo.get_by_id(task.project_id)
            await self.audit_repo.log_action(
                organization_id=project.organization_id,  # type: ignore
                entity_type="comment",
                entity_id=comment.id,
                action="updated",
                actor_id=current_user.id,
                changes={"content": {"old": old_content, "new": updated_comment.content}},
            )

        return updated_comment

    async def delete_comment(
        self, comment_id: uuid.UUID, current_user: User
    ) -> None:
        comment = await self.comment_repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        task = await self.task_repo.get_by_id(comment.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        role = await self._check_permission(task.project_id, current_user, Permission.COMMENT_READ)
        
        if not current_user.is_superuser:
            if comment.author_id != current_user.id:
                if not project_role_has_permission(ProjectRole(role), Permission.COMMENT_DELETE_ANY):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have permission to delete this comment."
                    )

        project = await self.project_repo.get_by_id(task.project_id)
        await self.audit_repo.log_action(
            organization_id=project.organization_id,  # type: ignore
            entity_type="comment",
            entity_id=comment.id,
            action="deleted",
            actor_id=current_user.id,
            changes=None,
        )

        await self.comment_repo.delete(comment)
