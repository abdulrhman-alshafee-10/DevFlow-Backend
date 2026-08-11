"""
app/api/v1/users.py
───────────────────
User CRUD endpoints — Phase 4 (authorization hardened).

Authorization rules applied in this phase:
  GET  /users          → Superuser only (system admin view)
  GET  /users/{id}     → Must be the target user OR a superuser
  PATCH /users/{id}    → Must be the target user OR a superuser
  DELETE /users/{id}   → Must be the target user OR a superuser

All endpoints require a valid JWT (enforced via router-level dependency).

Phase 5+ will add:
  - Organization membership checks
  - Project membership checks
  - Role-based permission requirements

Endpoint anatomy:
  Router → Service → Repository → Database
  │                                      │
  └── HTTP boundary (Pydantic in/out) ──┘
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SuperuserDep, get_current_user
from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


# ── Dependency ────────────────────────────────────────────────────────────────

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


# ── Authorization helpers ─────────────────────────────────────────────────────

def _require_self_or_superuser(
    user_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """
    Raise 403 unless the requesting user is either:
      a) The target user themselves (ownership).
      b) A superuser (system admin).

    This prevents IDOR (Insecure Direct Object Reference) — users cannot
    read or modify other users' profiles by simply knowing their UUID.
    """
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this user's data.",
        )


# ── LIST ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users (superuser only)",
)
async def list_users(
    current_user: SuperuserDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    """
    Paginated list of all users. Restricted to superusers.

    Regular users should not be able to enumerate all accounts — this is
    both a privacy concern and a reconnaissance risk.
    """
    users, total = await service.list_users(page=page, size=size)
    return PaginatedResponse[UserResponse].create(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


# ── GET BY ID ─────────────────────────────────────────────────────────────────

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID (self or superuser)",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Retrieve a single user by UUID.

    - Regular users can only access their own profile.
    - Superusers can access any profile.
    """
    _require_self_or_superuser(user_id, current_user)
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user profile (self or superuser)",
)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Partially update a user's profile fields.

    - Users can only update their own profile.
    - Superusers can update any profile.

    Only `full_name` and `avatar_url` can be changed here. Email/username
    changes require dedicated verification endpoints (Phase 3+).
    """
    _require_self_or_superuser(user_id, current_user)
    user = await service.update(user_id, data)
    return UserResponse.model_validate(user)


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (self or superuser)",
)
async def delete_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    service: UserService = Depends(get_user_service),
) -> None:
    """
    Permanently delete a user account.

    - Users can delete their own account.
    - Superusers can delete any account.
    """
    _require_self_or_superuser(user_id, current_user)
    await service.delete(user_id)
