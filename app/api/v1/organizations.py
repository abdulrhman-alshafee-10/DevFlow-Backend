"""
app/api/v1/organizations.py
────────────────────────────
All organization-related endpoints for Phase 5.

Two routers are defined:
  org_router  → /organizations  (org CRUD + members + org-scoped invitations)
  inv_router  → /invitations    (token-based invite actions + my-pending list)

Both are exported and included in v1_router via __init__.py.

Authorization summary:
  Create org         → any authenticated user
  Read/update org    → org member (role checked in service)
  Delete org         → OWNER only (service)
  Member list        → org:members:read
  Update role        → org:members:update_role
  Remove member      → org:members:remove
  Invite             → org:members:invite
  Cancel invite      → org:members:invite
  Accept/reject      → the invitee (verified by email match in service)
  My invites         → any authenticated user
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, OrgMemberDep, get_current_user, get_org_member_repository, get_org_repository
from app.core.roles import OrgRole
from app.database import get_db
from app.repositories.organization import (
    InvitationRepository,
    OrganizationMemberRepository,
    OrganizationRepository,
)
from app.schemas.common import PaginatedResponse
from app.schemas.organization import (
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationResponse,
    MemberRoleUpdate,
    OrganizationCreate,
    OrganizationMemberResponse,
    OrganizationResponse,
    OrganizationSummary,
    OrganizationUpdate,
)
from app.services.organization import OrganizationService


# ── Dependency factories ───────────────────────────────────────────────────────

def get_invite_repository(db: AsyncSession = Depends(get_db)) -> InvitationRepository:
    return InvitationRepository(db)


def get_org_service(
    db: AsyncSession = Depends(get_db),
) -> OrganizationService:
    return OrganizationService(
        org_repo=OrganizationRepository(db),
        member_repo=OrganizationMemberRepository(db),
        invite_repo=InvitationRepository(db),
    )


# ── Routers ────────────────────────────────────────────────────────────────────

org_router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    dependencies=[Depends(get_current_user)],
)

inv_router = APIRouter(
    prefix="/invitations",
    tags=["invitations"],
    dependencies=[Depends(get_current_user)],
)


# ══════════════════════════════════════════════════════════════════════════════
# ORGANIZATION CRUD
# ══════════════════════════════════════════════════════════════════════════════

@org_router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    data: OrganizationCreate,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationResponse:
    """
    Create a new organization. The authenticated user becomes the OWNER.

    - **name**: human-readable display name (required)
    - **slug**: URL-safe handle (auto-generated from name if omitted)
    - **description**: optional text
    - **avatar_url**: optional URL to the org's avatar image
    """
    org = await service.create_org(data, current_user)
    member_count = await OrganizationRepository(service.org_repo.session).get_member_count(org.id)
    return OrganizationResponse(
        **{k: getattr(org, k) for k in org.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        member_count=member_count,
        my_role=OrgRole.OWNER.value,
    )


@org_router.get(
    "",
    response_model=PaginatedResponse[OrganizationSummary],
    summary="List my organizations",
)
async def list_my_organizations(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: OrganizationService = Depends(get_org_service),
) -> PaginatedResponse[OrganizationSummary]:
    """
    Return all organizations the authenticated user belongs to.

    Includes the user's role in each organization via `my_role`.
    """
    orgs, total = await service.list_my_orgs(current_user, page=page, size=size)

    items = []
    for org in orgs:
        role = await service.member_repo.get_user_role(org.id, current_user.id)
        items.append(
            OrganizationSummary(
                id=org.id,
                name=org.name,
                slug=org.slug,
                avatar_url=org.avatar_url,
                is_active=org.is_active,
                my_role=role,
            )
        )
    return PaginatedResponse[OrganizationSummary].create(
        items=items, total=total, page=page, size=size
    )


@org_router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization details",
)
async def get_organization(
    ctx: OrgMemberDep,
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationResponse:
    """
    Retrieve full details of an organization.

    The caller must be a member. Returns their role as `my_role`.
    """
    org, membership = ctx
    member_count = await service.org_repo.get_member_count(org.id)
    return OrganizationResponse(
        **{k: getattr(org, k) for k in org.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        member_count=member_count,
        my_role=membership.role,
    )


@org_router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization details",
)
async def update_organization(
    data: OrganizationUpdate,
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationResponse:
    """
    Partially update an organization.

    Requires the `org:update` permission (ADMIN or OWNER).
    """
    org, membership = ctx
    updated_org = await service.update_org(org.id, data, current_user)
    member_count = await service.org_repo.get_member_count(updated_org.id)
    return OrganizationResponse(
        **{k: getattr(updated_org, k) for k in updated_org.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        member_count=member_count,
        my_role=membership.role,
    )


@org_router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization (OWNER only)",
)
async def delete_organization(
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> None:
    """
    Permanently delete an organization and all associated data.

    Only the organization OWNER can perform this action.
    This is irreversible — all projects, tasks, and members are removed.
    """
    org, _ = ctx
    await service.delete_org(org.id, current_user)


# ══════════════════════════════════════════════════════════════════════════════
# MEMBER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@org_router.get(
    "/{org_id}/members",
    response_model=PaginatedResponse[OrganizationMemberResponse],
    summary="List organization members",
)
async def list_members(
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    service: OrganizationService = Depends(get_org_service),
) -> PaginatedResponse[OrganizationMemberResponse]:
    """
    Return a paginated list of all members in the organization.

    Requires `org:members:read` permission (any org member).
    """
    org, _ = ctx
    members, total = await service.list_members(org.id, current_user, page=page, size=size)
    return PaginatedResponse[OrganizationMemberResponse].create(
        items=[OrganizationMemberResponse(**m) for m in members],
        total=total,
        page=page,
        size=size,
    )


@org_router.patch(
    "/{org_id}/members/{user_id}",
    response_model=OrganizationMemberResponse,
    summary="Update a member's role",
)
async def update_member_role(
    user_id: uuid.UUID,
    data: MemberRoleUpdate,
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> OrganizationMemberResponse:
    """
    Change a member's role within the organization.

    Rules enforced:
    - You cannot change your own role.
    - You cannot assign a role higher than your own (escalation prevention).
    - The last OWNER cannot be demoted.
    """
    org, _ = ctx
    updated = await service.update_member_role(org.id, user_id, data.role, current_user)
    # Re-fetch user details for the response
    members, _ = await service.member_repo.list_members(org.id, offset=0, limit=1000)
    member_dict = next((m for m in members if m["user_id"] == updated.user_id), None)
    if member_dict is None:
        # Fallback: return minimal info
        return OrganizationMemberResponse(
            user_id=updated.user_id,
            email="",
            username="",
            full_name=None,
            avatar_url=None,
            role=updated.role,
            joined_at=updated.joined_at,
        )
    return OrganizationMemberResponse(**member_dict)


@org_router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from the organization",
)
async def remove_member(
    user_id: uuid.UUID,
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> None:
    """
    Remove a member from the organization.

    - Requires `org:members:remove` permission.
    - Cannot remove the OWNER.
    """
    org, _ = ctx
    await service.remove_member(org.id, user_id, current_user)


# ══════════════════════════════════════════════════════════════════════════════
# ORG-SCOPED INVITATIONS
# ══════════════════════════════════════════════════════════════════════════════

@org_router.post(
    "/{org_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an invitation to join the organization",
)
async def send_invitation(
    data: InvitationCreate,
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    service: OrganizationService = Depends(get_org_service),
) -> InvitationResponse:
    """
    Send an email invitation to join the organization.

    - Requires `org:members:invite` permission.
    - Cannot invite someone as OWNER (direct ownership transfer is separate).
    - Returns 409 if a pending invitation already exists for that email.
    """
    org, _ = ctx
    invitation = await service.send_invitation(org.id, data, current_user, background_tasks)
    return InvitationResponse(
        **{k: getattr(invitation, k) for k in invitation.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
        organization_name=org.name,
    )


@org_router.get(
    "/{org_id}/invitations",
    response_model=PaginatedResponse[InvitationResponse],
    summary="List pending invitations for the organization",
)
async def list_org_invitations(
    ctx: OrgMemberDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=100),
    service: OrganizationService = Depends(get_org_service),
) -> PaginatedResponse[InvitationResponse]:
    """
    List all pending, non-expired invitations for the organization.

    Requires `org:members:invite` permission.
    """
    org, _ = ctx
    invitations, total = await service.list_org_invitations(
        org.id, current_user, page=page, size=size
    )
    items = [
        InvitationResponse(
            **{k: getattr(inv, k) for k in inv.__mapper__.column_attrs.keys()},  # type: ignore[union-attr]
            organization_name=org.name,
        )
        for inv in invitations
    ]
    return PaginatedResponse[InvitationResponse].create(
        items=items, total=total, page=page, size=size
    )


# ══════════════════════════════════════════════════════════════════════════════
# TOKEN-BASED INVITATION ACTIONS  (prefix: /invitations)
# ══════════════════════════════════════════════════════════════════════════════

@inv_router.get(
    "/pending",
    response_model=PaginatedResponse[InvitationResponse],
    summary="List my pending invitations",
)
async def my_pending_invitations(
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: OrganizationService = Depends(get_org_service),
) -> PaginatedResponse[InvitationResponse]:
    """
    Return all pending invitations addressed to the current user's email.

    Useful for a notification badge or an "invitations" inbox page.
    """
    invitations, total = await service.get_my_pending_invitations(
        current_user, page=page, size=size
    )
    items = [
        InvitationResponse(
            **{k: getattr(inv, k) for k in inv.__mapper__.column_attrs.keys()}  # type: ignore[union-attr]
        )
        for inv in invitations
    ]
    return PaginatedResponse[InvitationResponse].create(
        items=items, total=total, page=page, size=size
    )


@inv_router.post(
    "/{token}/accept",
    response_model=InvitationAcceptResponse,
    summary="Accept an invitation",
)
async def accept_invitation(
    token: str,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> InvitationAcceptResponse:
    """
    Accept an invitation using the token from the invitation email.

    The token is tied to an email address — only the invitee can use it.
    On success, the user becomes a member of the organization with the
    role specified in the invitation.
    """
    org, membership = await service.accept_invitation(token, current_user)
    return InvitationAcceptResponse(
        organization_id=org.id,
        organization_name=org.name,
        role=membership.role,
        joined_at=membership.joined_at,
    )


@inv_router.post(
    "/{token}/reject",
    response_model=InvitationResponse,
    summary="Reject an invitation",
)
async def reject_invitation(
    token: str,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> InvitationResponse:
    """
    Reject an invitation. The invitation status is set to 'rejected'.
    """
    invitation = await service.reject_invitation(token, current_user)
    return InvitationResponse(
        **{k: getattr(invitation, k) for k in invitation.__mapper__.column_attrs.keys()}  # type: ignore[union-attr]
    )


@inv_router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an invitation",
)
async def cancel_invitation(
    invitation_id: uuid.UUID,
    current_user: CurrentUser,
    service: OrganizationService = Depends(get_org_service),
) -> None:
    """
    Cancel a pending invitation (org admin/owner action).

    Requires `org:members:invite` permission on the org the invitation belongs to.
    Only pending invitations can be cancelled.
    """
    await service.cancel_invitation(invitation_id, current_user)
