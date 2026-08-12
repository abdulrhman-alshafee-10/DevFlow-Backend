"""
app/api/v1/auth.py
──────────────────
Authentication endpoints (register, login, refresh, logout, etc.)
and superuser admin endpoints (promote, demote).
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SuperuserDep, get_auth_service
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.services.user import UserService
from app.schemas.auth import LoginRequest
from app.core.rate_limit import RateLimiter

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


# ── Cookie helpers ────────────────────────────────────────────────────────────

def set_refresh_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/api/v1/auth",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

def clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )


# ── Authentication endpoints ──────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(limit=3, window=3600, tier="registration"))]
)
async def register(req: RegisterRequest, auth_service: AuthServiceDep):
    """Register a new user account."""
    return await auth_service.register_user(req)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(RateLimiter(limit=5, window=900, tier="auth"))]
)
async def login(
    req: Request,
    response: Response,
    json_data: LoginRequest,
    auth_service: AuthServiceDep,
):
    """
    Login via JSON body to get access and refresh tokens.

    The access token is returned in the response body.
    The refresh token is set as an HTTPOnly cookie.

    For Swagger UI testing, use `POST /api/v1/auth/token` instead (OAuth2 form).
    """
    ip_address = req.client.host if req.client else None
    device_info = req.headers.get("user-agent")

    access_token, refresh_token = await auth_service.login(json_data, device_info, ip_address)
    set_refresh_token_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post(
    "/token",
    response_model=TokenResponse,
    include_in_schema=True,
    summary="Login via OAuth2 form (Swagger UI only)",
    dependencies=[Depends(RateLimiter(limit=5, window=900, tier="auth"))]
)
async def login_swagger(
    req: Request,
    response: Response,
    auth_service: AuthServiceDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    OAuth2-compatible login endpoint for Swagger UI's 'Authorize' button.

    Accepts `username` (email) and `password` as form fields.
    Regular API clients should use `POST /auth/login` with a JSON body instead.
    """
    login_req = LoginRequest(email=form_data.username, password=form_data.password)
    ip_address = req.client.host if req.client else None
    device_info = req.headers.get("user-agent")

    access_token, refresh_token = await auth_service.login(login_req, device_info, ip_address)
    set_refresh_token_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    auth_service: AuthServiceDep,
    refresh_token: str | None = Cookie(default=None),
):
    """Refresh the access token using the refresh token from cookies."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    access_token, new_refresh_token = await auth_service.refresh_tokens(refresh_token)
    set_refresh_token_cookie(response, new_refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    response: Response,
    auth_service: AuthServiceDep,
    current_user: CurrentUser,
    refresh_token: str | None = Cookie(default=None),
):
    """Revoke the current session's refresh token and clear the cookie."""
    if refresh_token:
        await auth_service.logout(refresh_token)
    clear_refresh_token_cookie(response)
    return {"detail": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    auth_service: AuthServiceDep,
    current_user: CurrentUser,
):
    """Revoke ALL refresh tokens for the current user (logout from all devices)."""
    await auth_service.logout_all(current_user.id)
    clear_refresh_token_cookie(response)
    return {"detail": "Logged out of all devices successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get the current authenticated user's profile."""
    return current_user


# ── Superuser Admin Endpoints (Phase 4) ──────────────────────────────────────

@router.patch(
    "/admin/users/{user_id}/promote",
    response_model=UserResponse,
    summary="Promote a user to superuser (superuser only)",
)
async def promote_user(
    user_id: uuid.UUID,
    current_user: SuperuserDep,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Grant superuser (system admin) privileges to a user.

    Restricted to existing superusers. This is the bootstrap mechanism for
    creating additional system administrators.

    Note: To create the FIRST superuser, set `is_superuser = true` directly
    in the database (e.g. via psql or a seed script).
    """
    user = await service.promote_to_superuser(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/admin/users/{user_id}/demote",
    response_model=UserResponse,
    summary="Revoke superuser privileges from a user (superuser only)",
)
async def demote_user(
    user_id: uuid.UUID,
    current_user: SuperuserDep,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Revoke superuser privileges from a user.

    A superuser cannot demote themselves — this prevents lockout.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own superuser privileges.",
        )
    user = await service.demote_from_superuser(user_id)
    return UserResponse.model_validate(user)
