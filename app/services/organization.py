"""
app/services/organization.py
─────────────────────────────
Business logic for the entire organizations feature.

All methods in OrganizationService:
  create_org              — create org + add creator as OWNER (atomic)
  get_org                 — fetch org + caller's role
  update_org              — PATCH a field
  delete_org              — hard-delete (OWNER only)
  list_my_orgs            — orgs current user belongs to
  list_members            — paginated member list
  update_member_role      — role change with escalation prevention
  remove_member           — cannot remove the last OWNER
  send_invitation         — create token, fire background email
  accept_invitation       — validate token → create membership
  reject_invitation       — set status=rejected
  cancel_invitation       — org admin cancels a pending invite
  get_my_pending_invites  — invitations addressed to current user

Business rules enforced here (not in the router):
  - slug uniqueness
  - OWNER protection (cannot be removed or demoted)
  - role escalation prevention (can_assign_org_role)
  - invitation de-duplication
  - invitation expiry check
  - only the invitee (by email) can accept/reject
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks

from app.core.roles import OrgRole, Permission, can_assign_org_role, org_role_has_permission
from app.exceptions import (
    AlreadyExistsError,
    BusinessRuleError,
    InsufficientPermissionsError,
    NotFoundError,
)
from app.models.organization import Invitation, InvitationStatus, Organization, OrganizationMember
from app.models.user import User
from app.repositories.organization import (
    InvitationRepository,
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.repositories.user import UserRepository
from app.repositories.notification import NotificationRepository
from app.schemas.organization import (
    InvitationCreate,
    OrganizationCreate,
    OrganizationUpdate,
)
from app.utils.email import send_email
from app.core.cache import CacheManager

# Invitations expire after 7 days
INVITATION_TTL_DAYS = 7


class OrganizationService:
    """
    Orchestrates all organization-related operations.

    Dependencies (injected):
        org_repo     — OrganizationRepository
        member_repo  — OrganizationMemberRepository
        invite_repo  — InvitationRepository
    """

    def __init__(
        self,
        org_repo: OrganizationRepository,
        member_repo: OrganizationMemberRepository,
        invite_repo: InvitationRepository,
        user_repo: UserRepository,
        notification_repo: NotificationRepository,
    ) -> None:
        self.org_repo = org_repo
        self.member_repo = member_repo
        self.invite_repo = invite_repo
        self.user_repo = user_repo
        self.notification_repo = notification_repo

    # ─── Internal helpers ──────────────────────────────────────────────────────

    async def _get_org_or_404(self, org_id: uuid.UUID) -> Organization:
        org = await self.org_repo.get_by_id(org_id)
        if org is None:
            raise NotFoundError("Organization not found.", error_code="ORG_NOT_FOUND")
        return org

    async def _get_membership_or_403(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMember:
        membership = await self.member_repo.get_membership(org_id, user_id)
        if membership is None:
            raise InsufficientPermissionsError("You are not a member of this organization.")
        return membership

    def _require_permission(self, role: OrgRole, permission: Permission) -> None:
        if not org_role_has_permission(role, permission):
            raise InsufficientPermissionsError(permission.value)

    # ─── Organizations ─────────────────────────────────────────────────────────

    async def create_org(
        self, data: OrganizationCreate, creator: User
    ) -> Organization:
        """
        Create a new organization and automatically add the creator as OWNER.

        Both operations are in the same DB session/transaction so if either
        fails they both roll back.
        """
        slug = data.resolved_slug()

        if await self.org_repo.slug_exists(slug):
            raise AlreadyExistsError(f"Organization slug '{slug}'")

        org = await self.org_repo.create(
            name=data.name,
            slug=slug,
            description=data.description,
            avatar_url=data.avatar_url,
            created_by=creator.id,
        )

        # Creator always becomes OWNER — done atomically in the same transaction
        await self.member_repo.create(
            organization_id=org.id,
            user_id=creator.id,
            role=OrgRole.OWNER.value,
        )

        return org

    async def get_org(
        self, org_id: uuid.UUID, current_user: User
    ) -> tuple[Organization, OrganizationMember]:
        """
        Fetch an org and verify the caller is a member.
        Returns (org, membership) so callers can inspect the role.
        """
        org = await self._get_org_or_404(org_id)
        membership = await self._get_membership_or_403(org_id, current_user.id)
        return org, membership

    async def update_org(
        self,
        org_id: uuid.UUID,
        data: OrganizationUpdate,
        current_user: User,
    ) -> Organization:
        org, membership = await self.get_org(org_id, current_user)
        self._require_permission(OrgRole(membership.role), Permission.ORG_UPDATE)

        update_kwargs = data.model_dump(exclude_none=True)
        if not update_kwargs:
            return org

        updated_org = await self.org_repo.update(org, **update_kwargs)
        await CacheManager.delete(f"org:{org_id}")
        return updated_org

    async def delete_org(self, org_id: uuid.UUID, current_user: User) -> None:
        org, membership = await self.get_org(org_id, current_user)
        if OrgRole(membership.role) != OrgRole.OWNER:
            raise InsufficientPermissionsError(Permission.ORG_DELETE.value)
        await self.org_repo.delete(org)
        await CacheManager.delete(f"org:{org_id}")

    async def list_my_orgs(
        self, current_user: User, page: int = 1, size: int = 20
    ) -> tuple[list[Organization], int]:
        offset = (page - 1) * size
        return await self.org_repo.list_for_user(current_user.id, offset=offset, limit=size)

    # ─── Members ───────────────────────────────────────────────────────────────

    async def list_members(
        self,
        org_id: uuid.UUID,
        current_user: User,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[dict], int]:
        _, membership = await self.get_org(org_id, current_user)
        self._require_permission(OrgRole(membership.role), Permission.ORG_MEMBERS_READ)
        offset = (page - 1) * size
        return await self.member_repo.list_members(org_id, offset=offset, limit=size)

    async def update_member_role(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role: OrgRole,
        current_user: User,
    ) -> OrganizationMember:
        _, my_membership = await self.get_org(org_id, current_user)
        my_role = OrgRole(my_membership.role)
        self._require_permission(my_role, Permission.ORG_MEMBERS_UPDATE_ROLE)

        # Cannot change your own role
        if target_user_id == current_user.id:
            raise BusinessRuleError("You cannot change your own role.")

        # Escalation prevention
        if not can_assign_org_role(my_role, new_role):
            raise BusinessRuleError(
                f"You cannot assign the role '{new_role.value}' — "
                f"it is equal to or higher than your own role."
            )

        target_membership = await self.member_repo.get_membership(org_id, target_user_id)
        if target_membership is None:
            raise NotFoundError("Target user is not a member of this organization.")

        # OWNER demotion check
        if OrgRole(target_membership.role) == OrgRole.OWNER:
            owner_count = await self.member_repo.count_owners(org_id)
            if owner_count <= 1:
                raise BusinessRuleError(
                    "Cannot demote the last OWNER. Transfer ownership first."
                )

        updated_membership = await self.member_repo.update(target_membership, role=new_role.value)
        
        # Notify user of role change
        await self.notification_repo.create(
            user_id=target_user_id,
            organization_id=org_id,
            type="member_role_changed",
            title=f"Your role in '{my_membership.organization.name if hasattr(my_membership, 'organization') and my_membership.organization else 'the organization'}' changed to {new_role.value}",
            data={"organization_id": str(org_id), "new_role": new_role.value, "actor_id": str(current_user.id)}
        )
        
        await CacheManager.delete(f"org_member:{org_id}:{target_user_id}")
        return updated_membership

    async def remove_member(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        current_user: User,
    ) -> None:
        _, my_membership = await self.get_org(org_id, current_user)
        self._require_permission(OrgRole(my_membership.role), Permission.ORG_MEMBERS_REMOVE)

        target_membership = await self.member_repo.get_membership(org_id, target_user_id)
        if target_membership is None:
            raise NotFoundError("Target user is not a member of this organization.")

        # OWNER protection
        if OrgRole(target_membership.role) == OrgRole.OWNER:
            raise BusinessRuleError(
                "Cannot remove an OWNER from the organization. "
                "Transfer ownership before removing this member."
            )

        await self.member_repo.delete(target_membership)
        await CacheManager.delete(f"org_member:{org_id}:{target_user_id}")

    # ─── Invitations ───────────────────────────────────────────────────────────

    async def send_invitation(
        self,
        org_id: uuid.UUID,
        data: InvitationCreate,
        current_user: User,
        background_tasks: BackgroundTasks,
    ) -> Invitation:
        """
        Create an invitation and queue an email as a background task.

        Raises:
          409 — if there's already a pending, non-expired invite for this email+org
          403 — if caller lacks ORG_MEMBERS_INVITE
        """
        org, membership = await self.get_org(org_id, current_user)
        self._require_permission(OrgRole(membership.role), Permission.ORG_MEMBERS_INVITE)

        # Escalation check: cannot invite someone to a higher role than your own
        if not can_assign_org_role(OrgRole(membership.role), data.role):
            raise BusinessRuleError(
                f"You cannot invite someone as '{data.role.value}' — "
                "that role is higher than your own."
            )

        email = data.email.lower()

        # De-duplication: block duplicate pending invites
        existing = await self.invite_repo.get_pending_by_email_and_org(org_id, email)
        if existing is not None:
            raise AlreadyExistsError(
                f"A pending invitation already exists for '{email}' in this organization."
            )

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=INVITATION_TTL_DAYS)

        invitation = await self.invite_repo.create(
            organization_id=org_id,
            email=email,
            role=data.role.value,
            invited_by=current_user.id,
            token=token,
            status=InvitationStatus.PENDING.value,
            expires_at=expires_at,
        )

        # Fire email as a background task so the HTTP response isn't delayed
        invitation_link = f"https://app.devflow.com/invitations/{token}/accept"
        background_tasks.add_task(
            send_email,
            email_to=email,
            subject=f"You've been invited to join {org.name} on DevFlow",
            body=(
                f"<p>You've been invited to join <strong>{org.name}</strong> "
                f"as a <strong>{data.role.value}</strong>.</p>"
                f"<p><a href='{invitation_link}'>Accept Invitation</a></p>"
                f"<p>This link expires in {INVITATION_TTL_DAYS} days.</p>"
            ),
        )
        
        # Notify user in-app if they exist
        invited_user = await self.user_repo.get_by_email(email)
        if invited_user:
            await self.notification_repo.create(
                user_id=invited_user.id,
                organization_id=org_id,
                type="invitation_received",
                title=f"You've been invited to join {org.name}",
                data={"organization_id": str(org_id), "inviter_name": current_user.full_name}
            )

        return invitation

    async def accept_invitation(
        self, token: str, current_user: User
    ) -> tuple[Organization, OrganizationMember]:
        """
        Accept a pending invitation:
          1. Validate token exists, is PENDING, and has not expired.
          2. Verify the current user's email matches the invitation email.
          3. Create OrganizationMember row.
          4. Mark invitation as ACCEPTED.

        Returns (org, new_membership).
        """
        invitation = await self.invite_repo.get_by_token(token)
        if invitation is None:
            raise NotFoundError("Invitation not found.")

        # Ownership check — only the invitee can accept
        if invitation.email != current_user.email.lower():
            raise InsufficientPermissionsError(
                "This invitation was not sent to your email address."
            )

        # Status check
        if invitation.status != InvitationStatus.PENDING.value:
            raise BusinessRuleError(
                f"This invitation has already been {invitation.status}."
            )

        # Expiry check
        if datetime.now(timezone.utc) > invitation.expires_at:
            await self.invite_repo.update(invitation, status=InvitationStatus.EXPIRED.value)
            raise BusinessRuleError("This invitation has expired.")

        # Already a member?
        existing = await self.member_repo.get_membership(
            invitation.organization_id, current_user.id
        )
        if existing is not None:
            raise AlreadyExistsError("You are already a member of this organization.")

        org = await self._get_org_or_404(invitation.organization_id)

        # Create membership and mark invitation as accepted (atomic in same session)
        new_member = await self.member_repo.create(
            organization_id=invitation.organization_id,
            user_id=current_user.id,
            role=invitation.role,
        )
        await self.invite_repo.update(invitation, status=InvitationStatus.ACCEPTED.value)
        
        # Notify inviter
        if invitation.invited_by:
            await self.notification_repo.create(
                user_id=invitation.invited_by,
                organization_id=invitation.organization_id,
                type="invitation_accepted",
                title=f"{current_user.full_name} accepted your invitation to join {org.name}",
                data={"organization_id": str(org.id), "accepted_by": str(current_user.id)}
            )

        await CacheManager.delete(f"org_member:{org.id}:{current_user.id}")
        return org, new_member

    async def reject_invitation(self, token: str, current_user: User) -> Invitation:
        """Mark a pending invitation as rejected."""
        invitation = await self.invite_repo.get_by_token(token)
        if invitation is None:
            raise NotFoundError("Invitation not found.")

        if invitation.email != current_user.email.lower():
            raise InsufficientPermissionsError(
                "This invitation was not sent to your email address."
            )

        if invitation.status != InvitationStatus.PENDING.value:
            raise BusinessRuleError(
                f"This invitation has already been {invitation.status}."
            )

        return await self.invite_repo.update(
            invitation, status=InvitationStatus.REJECTED.value
        )

    async def cancel_invitation(
        self,
        invitation_id: uuid.UUID,
        current_user: User,
    ) -> None:
        """
        Cancel (delete) a pending invitation.

        Requires ORG_MEMBERS_INVITE permission on the org the invitation belongs to.
        """
        invitation = await self.invite_repo.get_by_id(invitation_id)
        if invitation is None:
            raise NotFoundError("Invitation not found.")

        if invitation.status != InvitationStatus.PENDING.value:
            raise BusinessRuleError("Only pending invitations can be cancelled.")

        _, membership = await self.get_org(invitation.organization_id, current_user)
        self._require_permission(OrgRole(membership.role), Permission.ORG_MEMBERS_INVITE)

        await self.invite_repo.delete(invitation)

    async def get_my_pending_invitations(
        self, current_user: User, page: int = 1, size: int = 20
    ) -> tuple[list[Invitation], int]:
        """Return all pending invitations addressed to the current user's email."""
        offset = (page - 1) * size
        return await self.invite_repo.get_pending_for_email(
            current_user.email, offset=offset, limit=size
        )

    async def list_org_invitations(
        self,
        org_id: uuid.UUID,
        current_user: User,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[Invitation], int]:
        """Return pending invitations for an org (admin view)."""
        _, membership = await self.get_org(org_id, current_user)
        self._require_permission(OrgRole(membership.role), Permission.ORG_MEMBERS_INVITE)
        offset = (page - 1) * size
        return await self.invite_repo.get_pending_for_org(org_id, offset=offset, limit=size)
