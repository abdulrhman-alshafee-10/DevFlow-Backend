"""
app/models/project.py
──────────────────────
Models for Projects and Project Members.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Project(BaseModel):
    """
    Project model.
    A project belongs to an organization and contains tasks.
    """
    __tablename__ = "projects"

    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_project_org_slug"),
        Index("ix_project_org_slug", "organization_id", "slug"),
        Index("ix_project_organization_id", "organization_id"),
        Index("ix_project_created_by", "created_by"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # type: ignore[name-defined]
        "Organization", lazy="noload"
    )
    creator: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", foreign_keys=[created_by], lazy="noload"
    )
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} org={self.organization_id} slug={self.slug!r}>"


class ProjectMember(BaseModel):
    """
    Association table: User ↔ Project with a project-level role.
    """
    __tablename__ = "project_members"

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        Index("ix_project_member_user_id", "user_id"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="members", lazy="noload"
    )
    user: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<ProjectMember project={self.project_id} user={self.user_id} role={self.role!r}>"
