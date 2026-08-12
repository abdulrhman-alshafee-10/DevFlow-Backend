"""
app/schemas/organization.py
────────────────────────────
Pydantic schemas for Organization, OrganizationMember, and Invitation.

Request schemas (input):
  OrganizationCreate       — POST /organizations
  OrganizationUpdate       — PATCH /organizations/{id}
  MemberRoleUpdate         — PATCH /organizations/{id}/members/{user_id}
  InvitationCreate         — POST /organizations/{id}/invitations

Response schemas (output):
  OrganizationResponse     — full org details
  OrganizationSummary      — compact, used in list endpoints
  OrganizationMemberResponse — member details + user info
  InvitationResponse       — invitation details
"""

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.roles import OrgRole


# ── Helpers ────────────────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    """
    Convert a human-readable name into a URL-safe slug.

    Examples:
        "Acme Corp"  → "acme-corp"
        "My  Org!"   → "my-org"
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)      # strip non-word chars except hyphen
    slug = re.sub(r"[\s_]+", "-", slug)        # spaces/underscores → hyphens
    slug = re.sub(r"-+", "-", slug)            # collapse multiple hyphens
    return slug.strip("-")


# ── Organization ───────────────────────────────────────────────────────────────

class OrganizationCreate(BaseModel):
    """Payload for creating a new organization."""
    name: str = Field(..., min_length=2, max_length=255, description="Display name")
    slug: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="URL-safe slug. Auto-generated from name if omitted.",
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    description: str | None = Field(default=None, max_length=5000)
    avatar_url: str | None = Field(default=None, max_length=500)

    def resolved_slug(self) -> str:
        """Return the slug, auto-generating from name if not provided."""
        return self.slug or _slugify(self.name)


class OrganizationUpdate(BaseModel):
    """Payload for a partial update — all fields optional."""
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    avatar_url: str | None = Field(default=None, max_length=500)



class OrganizationResponse(BaseModel):
    """Full organization details returned to the client."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    avatar_url: str | None
    is_active: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    # Injected by the service/endpoint (not a DB column)
    member_count: int = 0
    # The calling user's role in this org (injected by service)
    my_role: str | None = None


class OrganizationSummary(BaseModel):
    """Compact org representation used in list responses."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    avatar_url: str | None
    is_active: bool
    my_role: str | None = None


# ── Member ─────────────────────────────────────────────────────────────────────

class OrganizationMemberResponse(BaseModel):
    """A single member in an organization's member list."""
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    email: str
    username: str
    full_name: str | None
    avatar_url: str | None
    role: str
    joined_at: datetime


class MemberRoleUpdate(BaseModel):
    """Payload for updating a member's role."""
    role: OrgRole = Field(..., description="New role to assign")


# ── Invitation ─────────────────────────────────────────────────────────────────

class InvitationCreate(BaseModel):
    """Payload for sending an invitation."""
    email: EmailStr = Field(..., description="Email address of the invitee")
    role: OrgRole = Field(
        default=OrgRole.MEMBER,
        description="Role to grant upon acceptance",
    )

    @field_validator("role")
    @classmethod
    def owner_cannot_be_invited(cls, v: OrgRole) -> OrgRole:
        """
        Prevent inviting someone directly as OWNER.
        OWNER status is only granted to the org creator.
        An existing OWNER must explicitly transfer ownership.
        """
        if v == OrgRole.OWNER:
            raise ValueError("Cannot invite a user directly as OWNER.")
        return v


class InvitationResponse(BaseModel):
    """Invitation details returned to the client."""
    model_config = {"from_attributes": True}

    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str | None = None  # injected by service
    email: str
    role: str
    invited_by: uuid.UUID | None
    status: str
    expires_at: datetime
    created_at: datetime


class InvitationAcceptResponse(BaseModel):
    """Response after accepting an invitation — shows the new membership."""
    organization_id: uuid.UUID
    organization_name: str
    role: str
    joined_at: datetime
