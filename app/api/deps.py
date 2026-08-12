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

from fastapi import Depends, HTTPException, status, Query, WebSocketException
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
from app.repositories.notification import NotificationRepository
from app.services.auth import AuthService
from app.services.notification import NotificationService
from app.utils.redis import get_redis_client
from app.utils.security import decode_access_token
from app.core.cache import CacheManager

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


def get_notification_repository(db: SessionDep) -> NotificationRepository:
    return NotificationRepository(db)

def get_notification_service(
    notification_repo: Annotated[NotificationRepository, Depends(get_notification_repository)],
) -> NotificationService:
    return NotificationService(notification_repo=notification_repo)


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

    async def fetch_user_dict():
        u = await user_repo.get_by_id(user_id)
        if not u:
            return None
        # Convert to dict to cache
        return {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "full_name": u.full_name,
            "avatar_url": u.avatar_url,
            "is_active": u.is_active,
            "is_email_verified": u.is_email_verified,
            "is_superuser": u.is_superuser,
            "hashed_password": u.hashed_password,
            "created_at": u.created_at.isoformat(),
            "updated_at": u.updated_at.isoformat(),
        }

    user_dict = await CacheManager.get_or_set(
        key=f"user_auth:{user_id}",
        fetch_func=fetch_user_dict,
        ttl=300
    )

    if user_dict is None:
        raise credentials_exception
    
    # Reconstruct detached user model
    from datetime import datetime
    user_dict["id"] = UUID(user_dict["id"])
    user_dict["created_at"] = datetime.fromisoformat(user_dict["created_at"])
    user_dict["updated_at"] = datetime.fromisoformat(user_dict["updated_at"])
    user = User(**user_dict)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_current_user_ws(
    token: str = Query(..., description="JWT token"),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Extracts the JWT from the query parameter 'token', decodes it,
    and returns the authenticated User.
    Raises WebSocketException if invalid.
    """
    exception = WebSocketException(
        code=status.WS_1008_POLICY_VIOLATION,
        reason="Could not validate credentials",
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise exception
        user_id = UUID(user_id_str)
    except Exception:
        raise exception

    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise exception

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
        # Fetch org
        async def fetch_org_dict():
            o = await org_repo.get_by_id(org_id)
            if not o:
                return None
            return {
                "id": str(o.id),
                "name": o.name,
                "slug": o.slug,
                "description": o.description,
                "avatar_url": o.avatar_url,
                "is_active": o.is_active,
                "created_by": str(o.created_by) if o.created_by else None,
                "created_at": o.created_at.isoformat(),
                "updated_at": o.updated_at.isoformat(),
            }
            
        org_dict = await CacheManager.get_or_set(
            key=f"org:{org_id}",
            fetch_func=fetch_org_dict,
            ttl=300
        )

        if org_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )
            
        from datetime import datetime
        org_dict["id"] = UUID(org_dict["id"])
        if org_dict["created_by"]:
            org_dict["created_by"] = UUID(org_dict["created_by"])
        org_dict["created_at"] = datetime.fromisoformat(org_dict["created_at"])
        org_dict["updated_at"] = datetime.fromisoformat(org_dict["updated_at"])
        org = Organization(**org_dict)

        # Superusers bypass membership checks
        if current_user.is_superuser:
            synthetic = OrganizationMember()
            synthetic.organization_id = org.id
            synthetic.user_id = current_user.id
            synthetic.role = OrgRole.OWNER.value
            return org, synthetic

        async def fetch_member_dict():
            m = await member_repo.get_membership(org.id, current_user.id)
            if not m:
                return None
            return {
                "id": str(m.id),
                "organization_id": str(m.organization_id),
                "user_id": str(m.user_id),
                "role": m.role,
                "joined_at": m.joined_at.isoformat(),
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
            }

        membership_dict = await CacheManager.get_or_set(
            key=f"org_member:{org.id}:{current_user.id}",
            fetch_func=fetch_member_dict,
            ttl=300
        )

        if membership_dict is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization.",
            )

        membership_dict["id"] = UUID(membership_dict["id"])
        membership_dict["organization_id"] = UUID(membership_dict["organization_id"])
        membership_dict["user_id"] = UUID(membership_dict["user_id"])
        membership_dict["joined_at"] = datetime.fromisoformat(membership_dict["joined_at"])
        membership_dict["created_at"] = datetime.fromisoformat(membership_dict["created_at"])
        membership_dict["updated_at"] = datetime.fromisoformat(membership_dict["updated_at"])
        membership = OrganizationMember(**membership_dict)

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
        
        async def fetch_project_dict():
            p = await project_repo.get_by_id(project_id)
            if not p:
                return None
            return {
                "id": str(p.id),
                "organization_id": str(p.organization_id),
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "is_active": p.is_active,
                "is_public": p.is_public,
                "created_by": str(p.created_by) if p.created_by else None,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }

        project_dict = await CacheManager.get_or_set(
            key=f"project:{project_id}",
            fetch_func=fetch_project_dict,
            ttl=300
        )

        if project_dict is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found.",
            )

        from datetime import datetime
        project_dict["id"] = UUID(project_dict["id"])
        project_dict["organization_id"] = UUID(project_dict["organization_id"])
        if project_dict["created_by"]:
            project_dict["created_by"] = UUID(project_dict["created_by"])
        project_dict["created_at"] = datetime.fromisoformat(project_dict["created_at"])
        project_dict["updated_at"] = datetime.fromisoformat(project_dict["updated_at"])
        project = Project(**project_dict)

        if current_user.is_superuser:
            synthetic = ProjectMember()
            synthetic.project_id = project.id
            synthetic.user_id = current_user.id
            synthetic.role = ProjectRole.MANAGER.value
            return project, synthetic

        async def fetch_member_dict():
            m = await member_repo.get_membership(project.id, current_user.id)
            if not m:
                return None
            return {
                "id": str(m.id),
                "project_id": str(m.project_id),
                "user_id": str(m.user_id),
                "role": m.role,
                "joined_at": m.joined_at.isoformat(),
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
            }
            
        membership_dict = await CacheManager.get_or_set(
            key=f"project_member:{project.id}:{current_user.id}",
            fetch_func=fetch_member_dict,
            ttl=300
        )

        if membership_dict is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project.",
            )
            
        membership_dict["id"] = UUID(membership_dict["id"])
        membership_dict["project_id"] = UUID(membership_dict["project_id"])
        membership_dict["user_id"] = UUID(membership_dict["user_id"])
        membership_dict["joined_at"] = datetime.fromisoformat(membership_dict["joined_at"])
        membership_dict["created_at"] = datetime.fromisoformat(membership_dict["created_at"])
        membership_dict["updated_at"] = datetime.fromisoformat(membership_dict["updated_at"])
        membership = ProjectMember(**membership_dict)

        return project, membership

ProjectMemberDep = Annotated[
    tuple[Project, ProjectMember],
    Depends(require_project_member()),
]

