"""
app/api/v1/users.py
───────────────────
User CRUD endpoints — Phase 2 (temporary, unprotected).

These endpoints exist so we can test the entire data layer stack
(schema → service → repository → database) before authentication exists.

In Phase 3, every endpoint gets wrapped with `Depends(get_current_user)`.
In Phase 4, specific roles are required for destructive operations.

Endpoint anatomy:
  Router → Service → Repository → Database
  │                                      │
  └── HTTP boundary (Pydantic in/out) ──┘

The router's job is thin:
  1. Parse and validate request (FastAPI + Pydantic do this automatically)
  2. Call the service
  3. Return the response with the right status code

It never talks to the database directly.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


# ── Dependency ────────────────────────────────────────────────────────────────
# Encapsulates service construction. Every endpoint that needs the UserService
# adds `Depends(get_user_service)` — the DB session is injected automatically.

def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description=(
        "Register a new user account. "
        "**Phase 2 only** — unprotected. Phase 3 will remove this endpoint "
        "and replace it with POST /auth/register."
    ),
)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(data)
    return UserResponse.model_validate(user)


# ── LIST ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List users (paginated)",
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
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
    summary="Get a user by ID",
)
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


# ── UPDATE ────────────────────────────────────────────────────────────────────

@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user (partial)",
)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.update(user_id, data)
    return UserResponse.model_validate(user)


# ── DELETE ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
    user_id: uuid.UUID,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete(user_id)
