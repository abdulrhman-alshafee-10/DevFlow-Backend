"""
app/api/deps.py
───────────────
FastAPI dependencies for authentication and authorization.

Dependency chain:
  get_db           → raw AsyncSession
  get_redis_client → raw Redis connection

  get_user_repository  → UserRepository(db)
  get_token_repository → RefreshTokenRepository(db)
  get_auth_service     → AuthService(user_repo, token_repo, redis)

  get_current_user     → decoded JWT → DB user (raises 401 if invalid)
  CurrentUser          → Annotated alias for the above

  require_superuser    → get_current_user + is_superuser check (403)
  require_verified_email → get_current_user + is_email_verified check (403)

  RequirePermission(perm) → dependency factory
    Phase 4: framework only — context (org_role / project_role) injected
             by Phases 5 & 6 when membership is established.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio.client import Redis

from app.core.roles import OrgRole, ProjectRole, Permission
from app.core.roles import org_role_has_permission, project_role_has_permission
from app.database import get_db
from app.exceptions import InsufficientPermissionsError, NotFoundError
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.repositories.organization import OrganizationMemberRepository, OrganizationRepository
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth import AuthService
from app.utils.redis import get_redis_client
from app.utils.security import decode_access_token

# The tokenUrl tells Swagger UI where to send the login request when clicking "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

SessionDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep   = Annotated[Redis, Depends(get_redis_client)]
TokenDep   = Annotated[str, Depends(oauth2_scheme)]


# ── Repository & Service Factories ────────────────────────────────────────────

def get_user_repository(db: SessionDep) -> UserRepository:
    return UserRepository(db)

def get_token_repository(db: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(db)

def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    token_repo: Annotated[RefreshTokenRepository, Depends(get_token_repository)],
    redis_client: RedisDep,
) -> AuthService:
    return AuthService(user_repo=user_repo, token_repo=token_repo, redis_client=redis_client)


# ── Core Authentication Dependency ────────────────────────────────────────────

async def get_current_user(
    token: TokenDep,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Extracts the JWT from the Authorization header, decodes it,
    and returns the authenticated User from the database.

    Raises:
        401 if the token is missing, malformed, or expired.
        400 if the user account is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except Exception:
        raise credentials_exception

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


# ── Superuser Dependency ───────────────────────────────────────────────────────

async def require_superuser(current_user: CurrentUser) -> User:
    """
    Dependency that restricts access to superusers only.

    Use this on system-administration endpoints (list all users, promote a user, etc.).

    Raises:
        403 Forbidden if the authenticated user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required.",
        )
    return current_user


SuperuserDep = Annotated[User, Depends(require_superuser)]


# ── Email-Verified Dependency ─────────────────────────────────────────────────

async def require_verified_email(current_user: CurrentUser) -> User:
    """
    Dependency that restricts access to users who have verified their email.

    Use this on sensitive operations (creating organizations, billing, etc.).

    Raises:
        403 Forbidden if the authenticated user's email is not verified.
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please verify your email address.",
        )
    return current_user


VerifiedUserDep = Annotated[User, Depends(require_verified_email)]


# ── Permission Dependency Factory ─────────────────────────────────────────────

class RequirePermission:
    """
    A dependency factory that checks whether the current user's role
    grants a specific permission.

    Phase 4 — Framework:
        The role context (org_role / project_role) is passed directly.
        Phases 5 & 6 will inject these from Organization/Project membership
        lookups via their own dependency chains.

    Usage (Phase 4 — explicit role, for testing/internal use):
        @router.get("/", dependencies=[Depends(RequirePermission(Permission.PROJECT_READ))])

    Usage (Phases 5+):
        The membership dependency resolves the role before this runs,
        so endpoint code never needs to think about role resolution.

    Raises:
        401 if the user is not authenticated.
        403 if the user's role doesn't have the required permission.
    """

    def __init__(self, permission: Permission) -> None:
        self.permission = permission

    async def __call__(
        self,
        current_user: CurrentUser,
        org_role: OrgRole | None = None,
        project_role: ProjectRole | None = None,
    ) -> User:
        """
        Check if the user has the required permission via their org or project role.

        Superusers always pass — they bypass permission checks.
        """
        # Superusers bypass all permission checks
        if current_user.is_superuser:
            return current_user

        # Check org-level role first
        if org_role is not None:
            if org_role_has_permission(org_role, self.permission):
                return current_user

        # Then check project-level role
        if project_role is not None:
            if project_role_has_permission(project_role, self.permission):
                return current_user

        # If neither role granted permission, deny access
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: '{self.permission.value}'.",
        )


# ── Organization Member Dependency ───────────────────────────────────────────────

def get_org_repository(db: SessionDep) -> OrganizationRepository:
    return OrganizationRepository(db)

def get_org_member_repository(db: SessionDep) -> OrganizationMemberRepository:
    return OrganizationMemberRepository(db)


class require_org_member:
    """
    Dependency factory that:
      1. Fetches the Organization by org_id path param.
      2. Looks up the OrganizationMember row for (current_user, org).
      3. Raises 404 if org doesn't exist, 403 if user isn't a member.
      4. Injects (org, membership) into the endpoint.

    Usage:
        @router.get("/{org_id}/members")
        async def list_members(
            ctx: Annotated[tuple[Organization, OrganizationMember],
                           Depends(require_org_member())],
        ):
            org, membership = ctx
            ...
    """

    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        org_id: UUID,
        current_user: CurrentUser,
        org_repo: Annotated[OrganizationRepository, Depends(get_org_repository)],
        member_repo: Annotated[OrganizationMemberRepository, Depends(get_org_member_repository)],
    ) -> tuple[Organization, OrganizationMember]:
        org = await org_repo.get_by_id(org_id)
        if org is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )

        # Superusers bypass membership checks
        if current_user.is_superuser:
            # Return a synthetic membership with OWNER role for superusers
            synthetic = OrganizationMember()
            synthetic.organization_id = org.id
            synthetic.user_id = current_user.id
            synthetic.role = OrgRole.OWNER.value
            return org, synthetic

        membership = await member_repo.get_membership(org.id, current_user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization.",
            )

        return org, membership


OrgMemberDep = Annotated[
    tuple[Organization, OrganizationMember],
    Depends(require_org_member()),
]


# ── Project Member Dependency ──────────────────────────────────────────────────

from app.models.project import Project, ProjectMember
from app.repositories.project import ProjectRepository, ProjectMemberRepository

def get_project_repository(db: SessionDep) -> ProjectRepository:
    return ProjectRepository(db)

def get_project_member_repository(db: SessionDep) -> ProjectMemberRepository:
    return ProjectMemberRepository(db)

class require_project_member:
    """
    Dependency factory that:
      1. Fetches the Project by project_id path param.
      2. Looks up the ProjectMember row for (current_user, project).
      3. Raises 404 if project doesn't exist, 403 if user isn't a member.
      4. Injects (project, membership) into the endpoint.
    """

    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        project_id: UUID,
        current_user: CurrentUser,
        project_repo: Annotated[ProjectRepository, Depends(get_project_repository)],
        member_repo: Annotated[ProjectMemberRepository, Depends(get_project_member_repository)],
    ) -> tuple[Project, ProjectMember]:
        project = await project_repo.get_by_id(project_id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        if current_user.is_superuser:
            synthetic = ProjectMember()
            synthetic.project_id = project.id
            synthetic.user_id = current_user.id
            synthetic.role = ProjectRole.MANAGER.value
            return project, synthetic

        membership = await member_repo.get_membership(project.id, current_user.id)
        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project.",
            )

        return project, membership

ProjectMemberDep = Annotated[
    tuple[Project, ProjectMember],
    Depends(require_project_member()),
]

