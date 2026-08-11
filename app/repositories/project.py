"""
app/repositories/project.py
───────────────────────────
Repositories for Project and ProjectMember models.
"""

import uuid
from typing import Any, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember
from app.models.user import User


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_slug(self, org_id: uuid.UUID, slug: str) -> Project | None:
        stmt = select(Project).where(
            Project.organization_id == org_id, Project.slug == slug
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        return project

    async def update(self, project: Project) -> Project:
        # Changes are already tracked by the session, just need to flush
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()

    async def list_by_organization(
        self, org_id: uuid.UUID, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Project], int]:
        # Get total count
        count_stmt = select(func.count()).select_from(Project).where(
            Project.organization_id == org_id
        )
        total = await self.session.scalar(count_stmt) or 0

        # Get items
        stmt = (
            select(Project)
            .where(Project.organization_id == org_id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        projects = result.scalars().all()

        return projects, total


class ProjectMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_membership(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectMember | None:
        stmt = select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_role(self, project_id: uuid.UUID, user_id: uuid.UUID) -> str | None:
        membership = await self.get_membership(project_id, user_id)
        return membership.role if membership else None

    async def get_member_count(self, project_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(ProjectMember).where(
            ProjectMember.project_id == project_id
        )
        return await self.session.scalar(stmt) or 0

    async def add_member(self, membership: ProjectMember) -> ProjectMember:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def update_role(self, membership: ProjectMember, new_role: str) -> ProjectMember:
        membership.role = new_role
        await self.session.flush()
        return membership

    async def remove_member(self, membership: ProjectMember) -> None:
        await self.session.delete(membership)
        await self.session.flush()

    async def list_members(
        self, project_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[dict[str, Any]], int]:
        # Count total
        count_stmt = select(func.count()).select_from(ProjectMember).where(
            ProjectMember.project_id == project_id
        )
        total = await self.session.scalar(count_stmt) or 0

        # Fetch joined with User
        stmt = (
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.added_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        # Format output
        members = []
        for membership, user in rows:
            members.append(
                {
                    "user_id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "avatar_url": user.avatar_url,
                    "role": membership.role,
                    "added_at": membership.added_at,
                }
            )

        return members, total
