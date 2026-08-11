"""
app/models/organization.py
──────────────────────────
Three models that together implement multi-tenant organizations in DevFlow.

  Organization      → the top-level tenant (e.g. "Acme Corp")
  OrganizationMember → join table: which users belong to which org, with a role
  Invitation         → time-limited email token to invite someone into an org

Design decisions:
  - slug is a URL-safe handle unique per org (e.g. "acme-corp").
    Auto-generated from name if the caller doesn't provide one.
  - OrganizationMember uses a composite UNIQUE(org_id, user_id) so a user
    can never appear twice in the same org.
  - Invitation.token is a cryptographically random secret (secrets.token_urlsafe).
    It is stored in plain text here because it acts as a bearer credential,
    not a password — it doesn't need bcrypt-style hashing.
  - InvitationStatus and OrgRole are str enums so they map to plain VARCHAR
    columns and stay readable in raw SQL queries.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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


# ── Status Enum ────────────────────────────────────────────────────────────────

class InvitationStatus(str, PyEnum):
    """Lifecycle states of an invitation."""
    PENDING  = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED  = "expired"


# ── Organization ───────────────────────────────────────────────────────────────

class Organization(BaseModel):
    """
    Top-level tenant entity.

    Every project, task, and resource in DevFlow lives inside exactly one
    Organization. All queries in subsequent phases are scoped by org_id
    to ensure complete data isolation between tenants.
    """
    __tablename__ = "organizations"

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="URL-safe unique handle, e.g. 'acme-corp'. Auto-generated from name.",
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    # ── Ownership ─────────────────────────────────────────────────────────────
    # Denormalized for fast lookups; membership table is authoritative for role.
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # nullable so the org survives if the creator account is deleted
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    creator: Mapped["User"] = relationship(             # type: ignore[name-defined]
        "User",
        foreign_keys=[created_by],
        back_populates="created_orgs",
        lazy="noload",
    )
    members: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Organization id={self.id} slug={self.slug!r}>"


# ── OrganizationMember ─────────────────────────────────────────────────────────

class OrganizationMember(BaseModel):
    """
    Association table: User ↔ Organization with a role.

    A user may belong to many organizations, each with a different role.
    The composite unique constraint prevents duplicate memberships.

    joined_at is distinct from created_at:
      - created_at → when the row was inserted (always)
      - joined_at  → when the user actually accepted/was added (same in practice,
                     but semantically cleaner and useful for audit displays)
    """
    __tablename__ = "organization_members"

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_member"),
        Index("ix_org_member_user_id", "user_id"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Role ──────────────────────────────────────────────────────────────────
    # Stored as a plain string matching OrgRole enum values ("owner", "admin", …)
    role: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="members", lazy="noload"
    )
    user: Mapped["User"] = relationship(           # type: ignore[name-defined]
        "User", back_populates="org_memberships", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<OrganizationMember org={self.organization_id} user={self.user_id} role={self.role!r}>"


# ── Invitation ─────────────────────────────────────────────────────────────────

class Invitation(BaseModel):
    """
    Time-limited email invitation to join an organization.

    Lifecycle:
      1. An ADMIN/OWNER calls POST /organizations/{id}/invitations
         → row created with status=PENDING and a random token
      2. The invitee receives an email with a link containing the token
      3. The invitee calls POST /invitations/{token}/accept (or /reject)
      4. On accept: OrganizationMember row is created, status → ACCEPTED
      5. Expired tokens (expires_at < now) are treated as EXPIRED by the service

    Security:
      - token is generated with secrets.token_urlsafe(32) → 256-bit entropy
      - token stored plaintext (it's a single-use bearer credential)
      - expires_at is enforced server-side, not just by the client
    """
    __tablename__ = "invitations"

    __table_args__ = (
        Index("ix_invitation_org_email", "organization_id", "email"),
        Index("ix_invitation_email", "email"),
    )

    # ── Organization + invited email ──────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")

    # ── Who sent the invite ───────────────────────────────────────────────────
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Token ─────────────────────────────────────────────────────────────────
    token: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # ── Status & expiry ───────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=InvitationStatus.PENDING.value,
        server_default="pending",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="invitations", lazy="noload"
    )
    inviter: Mapped["User"] = relationship(          # type: ignore[name-defined]
        "User",
        foreign_keys=[invited_by],
        back_populates="sent_invitations",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<Invitation id={self.id} email={self.email!r} "
            f"org={self.organization_id} status={self.status!r}>"
        )
