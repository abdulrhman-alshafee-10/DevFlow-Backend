"""
app/repositories/organization.py
─────────────────────────────────
Three repositories for the organization feature:

  OrganizationRepository       — CRUD for organizations table
  OrganizationMemberRepository — membership queries (role lookups, list, remove)
  InvitationRepository         — token-based invitation queries

All queries are scoped by organization_id where relevant — this is the
primary data-isolation boundary in DevFlow's multi-tenant architecture.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Invitation, InvitationStatus, Organization, OrganizationMember
from app.models.user import User
from app.repositories.base import BaseRepository


# ── OrganizationRepository ─────────────────────────────────────────────────────

class OrganizationRepository(BaseRepository[Organization]):
    """CRUD + custom queries for the organizations table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Organization, session)

    async def get_by_slug(self, slug: str) -> Organization | None:
        """Fetch an org by its URL slug."""
        result = await self.session.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        """Return True if the slug is already taken."""
        result = await self.session.execute(
            select(func.count()).select_from(Organization).where(Organization.slug == slug)
        )
        return (result.scalar_one() or 0) > 0

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Organization], int]:
        """
        Return organizations the given user is a member of.

        Joins org_members so we only return orgs the user actually belongs to.
        """
        base_q = (
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(OrganizationMember.user_id == user_id)
            .where(Organization.is_active == True)  # noqa: E712
        )

        count_result = await self.session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one() or 0

        result = await self.session.execute(
            base_q.order_by(Organization.created_at.desc()).offset(offset).limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_member_count(self, org_id: uuid.UUID) -> int:
        """Return the number of active members in an org."""
        result = await self.session.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
        )
        return result.scalar_one() or 0


# ── OrganizationMemberRepository ──────────────────────────────────────────────

class OrganizationMemberRepository(BaseRepository[OrganizationMember]):
    """Queries for the organization_members join table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(OrganizationMember, session)

    async def get_membership(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMember | None:
        """Return the membership row for (org, user) or None."""
        result = await self.session.execute(
            select(OrganizationMember).where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_role(self, org_id: uuid.UUID, user_id: uuid.UUID) -> str | None:
        """Return the role string for a user in an org, or None if not a member."""
        membership = await self.get_membership(org_id, user_id)
        return membership.role if membership else None

    async def list_members(
        self,
        org_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """
        Return members with their user profile details.

        Joins User so we can return email/username in one query, avoiding N+1.
        """
        base_q = (
            select(OrganizationMember, User)
            .join(User, User.id == OrganizationMember.user_id)
            .where(OrganizationMember.organization_id == org_id)
        )

        count_result = await self.session.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
        )
        total = count_result.scalar_one() or 0

        result = await self.session.execute(
            base_q.order_by(OrganizationMember.joined_at.asc()).offset(offset).limit(limit)
        )
        rows = result.all()

        members = [
            {
                "user_id": member.user_id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "role": member.role,
                "joined_at": member.joined_at,
            }
            for member, user in rows
        ]
        return members, total

    async def count_owners(self, org_id: uuid.UUID) -> int:
        """Count how many OWNERs an org has (must always be ≥ 1)."""
        result = await self.session.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(
                and_(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.role == "owner",
                )
            )
        )
        return result.scalar_one() or 0


# ── InvitationRepository ───────────────────────────────────────────────────────

class InvitationRepository(BaseRepository[Invitation]):
    """Queries for the invitations table."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Invitation, session)

    async def get_by_token(self, token: str) -> Invitation | None:
        """Fetch an invitation by its bearer token."""
        result = await self.session.execute(
            select(Invitation).where(Invitation.token == token)
        )
        return result.scalar_one_or_none()

    async def get_pending_for_org(
        self, org_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> tuple[list[Invitation], int]:
        """Return all pending (non-expired) invitations for an org."""
        now = datetime.now(timezone.utc)
        base_q = select(Invitation).where(
            and_(
                Invitation.organization_id == org_id,
                Invitation.status == InvitationStatus.PENDING.value,
                Invitation.expires_at > now,
            )
        )

        count_result = await self.session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one() or 0

        result = await self.session.execute(
            base_q.order_by(Invitation.created_at.desc()).offset(offset).limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_pending_by_email_and_org(
        self, org_id: uuid.UUID, email: str
    ) -> Invitation | None:
        """
        Return a pending invitation for a specific email+org combo.

        Used for duplicate-invitation detection.
        """
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Invitation).where(
                and_(
                    Invitation.organization_id == org_id,
                    Invitation.email == email.lower(),
                    Invitation.status == InvitationStatus.PENDING.value,
                    Invitation.expires_at > now,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_for_email(
        self, email: str, offset: int = 0, limit: int = 50
    ) -> tuple[list[Invitation], int]:
        """Return all pending invitations sent to a given email address."""
        now = datetime.now(timezone.utc)
        base_q = select(Invitation).where(
            and_(
                Invitation.email == email.lower(),
                Invitation.status == InvitationStatus.PENDING.value,
                Invitation.expires_at > now,
            )
        )

        count_result = await self.session.execute(
            select(func.count()).select_from(base_q.subquery())
        )
        total = count_result.scalar_one() or 0

        result = await self.session.execute(
            base_q.order_by(Invitation.created_at.desc()).offset(offset).limit(limit)
        )
        items = list(result.scalars().all())
        return items, total
