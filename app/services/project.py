"""
app/services/project.py
────────────────────────
Business logic for Projects.
"""

import uuid
from typing import Any, Sequence

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.core.roles import Permission, ProjectRole, project_role_has_permission, can_assign_project_role
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.repositories.project import ProjectMemberRepository, ProjectRepository
from app.repositories.organization import OrganizationMemberRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.core.cache import CacheManager


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        member_repo: ProjectMemberRepository,
        org_member_repo: OrganizationMemberRepository,
    ) -> None:
        self.project_repo = project_repo
        self.member_repo = member_repo
        self.org_member_repo = org_member_repo

    async def _check_permission(
        self, project_id: uuid.UUID, current_user: User, permission: Permission
    ) -> str:
        """
        Verify the user has the required permission in the project.
        Returns their project role.
        """
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

    async def create_project(
        self, org_id: uuid.UUID, data: ProjectCreate, current_user: User
    ) -> Project:
        if not current_user.is_superuser:
            org_membership = await self.org_member_repo.get_membership(org_id, current_user.id)
            if not org_membership:
                raise HTTPException(status_code=403, detail="You are not a member of this organization.")
            from app.core.roles import OrgRole, org_role_has_permission, Permission
            if not org_role_has_permission(OrgRole(org_membership.role), Permission.PROJECT_CREATE):
                raise HTTPException(status_code=403, detail=f"Permission denied. Required: '{Permission.PROJECT_CREATE.value}'.")

        project = Project(
            organization_id=org_id,
            name=data.name,
            slug=data.resolved_slug(),
            description=data.description,
            created_by=current_user.id,
        )

        try:
            created_project = await self.project_repo.create(project)
        except IntegrityError:
            await self.project_repo.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project with this slug already exists in the organization.",
            )

        # Add the creator as a MANAGER
        membership = ProjectMember(
            project_id=created_project.id,
            user_id=current_user.id,
            role=ProjectRole.MANAGER.value,
        )
        await self.member_repo.add_member(membership)
        
        return created_project

    async def list_org_projects(
        self, org_id: uuid.UUID, current_user: User, page: int = 1, size: int = 20
    ) -> tuple[Sequence[Project], int]:
        offset = (page - 1) * size
        return await self.project_repo.list_by_organization(
            org_id, offset=offset, limit=size
        )

    async def update_project(
        self, project_id: uuid.UUID, data: ProjectUpdate, current_user: User
    ) -> Project:
        await self._check_permission(project_id, current_user, Permission.PROJECT_UPDATE)

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description

        updated = await self.project_repo.update(project)
        await CacheManager.delete(f"project:{project_id}")
        return updated

    async def delete_project(self, project_id: uuid.UUID, current_user: User) -> None:
        await self._check_permission(project_id, current_user, Permission.PROJECT_DELETE)

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        await self.project_repo.delete(project)
        await CacheManager.delete(f"project:{project_id}")

    async def archive_project(self, project_id: uuid.UUID, current_user: User) -> Project:
        await self._check_permission(project_id, current_user, Permission.PROJECT_UPDATE)

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.status = "archived"
        updated = await self.project_repo.update(project)
        await CacheManager.delete(f"project:{project_id}")
        return updated

    async def unarchive_project(self, project_id: uuid.UUID, current_user: User) -> Project:
        await self._check_permission(project_id, current_user, Permission.PROJECT_UPDATE)

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        project.status = "active"
        updated = await self.project_repo.update(project)
        await CacheManager.delete(f"project:{project_id}")
        return updated

    # ── Membership ─────────────────────────────────────────────────────────────

    async def list_members(
        self, project_id: uuid.UUID, current_user: User, page: int = 1, size: int = 50
    ) -> tuple[list[dict[str, Any]], int]:
        await self._check_permission(project_id, current_user, Permission.PROJECT_READ)
        offset = (page - 1) * size
        
        async def fetch():
            return await self.member_repo.list_members(project_id, offset=offset, limit=size)
            
        res = await CacheManager.get_or_set(
            key=f"project_members_list:{project_id}:{page}:{size}",
            fetch_func=fetch,
            ttl=300
        )
        return res if res else ([], 0)

    async def add_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID, role: ProjectRole, current_user: User
    ) -> ProjectMember:
        my_role_str = await self._check_permission(project_id, current_user, Permission.PROJECT_MEMBERS_MANAGE)

        if not current_user.is_superuser:
            if not can_assign_project_role(ProjectRole(my_role_str), role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to assign the {role.value} role.",
                )

        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Must be org member first
        org_membership = await self.org_member_repo.get_membership(project.organization_id, user_id)
        if not org_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be a member of the organization to be added to the project.",
            )

        existing = await self.member_repo.get_membership(project_id, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this project.",
            )

        membership = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role.value,
        )
        added = await self.member_repo.add_member(membership)
        await CacheManager.delete(f"project_member:{project_id}:{user_id}")
        await CacheManager.delete_pattern(f"project_members_list:{project_id}:*")
        return added

    async def update_member_role(
        self, project_id: uuid.UUID, user_id: uuid.UUID, new_role: ProjectRole, current_user: User
    ) -> ProjectMember:
        my_role_str = await self._check_permission(project_id, current_user, Permission.PROJECT_MEMBERS_MANAGE)

        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot modify your own role.",
            )

        target_membership = await self.member_repo.get_membership(project_id, user_id)
        if not target_membership:
            raise HTTPException(status_code=404, detail="Member not found.")

        if not current_user.is_superuser:
            if not can_assign_project_role(ProjectRole(my_role_str), new_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to assign the {new_role.value} role.",
                )
            if not can_assign_project_role(ProjectRole(my_role_str), ProjectRole(target_membership.role)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to modify a user with the {target_membership.role} role.",
                )

        updated = await self.member_repo.update_role(target_membership, new_role.value)
        await CacheManager.delete(f"project_member:{project_id}:{user_id}")
        await CacheManager.delete_pattern(f"project_members_list:{project_id}:*")
        return updated

    async def remove_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID, current_user: User
    ) -> None:
        my_role_str = await self._check_permission(project_id, current_user, Permission.PROJECT_MEMBERS_MANAGE)

        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove yourself. Leave the project instead.",
            )

        target_membership = await self.member_repo.get_membership(project_id, user_id)
        if not target_membership:
            raise HTTPException(status_code=404, detail="Member not found.")

        if not current_user.is_superuser:
            if not can_assign_project_role(ProjectRole(my_role_str), ProjectRole(target_membership.role)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You do not have permission to remove a user with the {target_membership.role} role.",
                )

        await self.member_repo.remove_member(target_membership)
        await CacheManager.delete(f"project_member:{project_id}:{user_id}")
        await CacheManager.delete_pattern(f"project_members_list:{project_id}:*")
