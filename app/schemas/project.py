"""
app/schemas/project.py
──────────────────────
Pydantic schemas for Project and ProjectMember.
"""

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.roles import ProjectRole


def _slugify(name: str) -> str:
    """
    Convert a human-readable name into a URL-safe slug.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


# ── Project ────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = Field(default=None, max_length=5000)

    def resolved_slug(self) -> str:
        return self.slug or _slugify(self.name)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    # Note: 'status' (archived/active) is handled by separate endpoints /archive and /unarchive


class ProjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    
    # Injected by service
    my_role: str | None = None
    member_count: int = 0


class ProjectSummary(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    status: str
    my_role: str | None = None


# ── Project Member ─────────────────────────────────────────────────────────────

class ProjectMemberResponse(BaseModel):
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    avatar_url: str | None
    role: str
    added_at: datetime


class ProjectMemberAdd(BaseModel):
    user_id: uuid.UUID = Field(..., description="User ID from the organization to add to the project")
    role: ProjectRole = Field(default=ProjectRole.MEMBER, description="Role in the project")


class ProjectMemberUpdate(BaseModel):
    role: ProjectRole = Field(..., description="New role in the project")
