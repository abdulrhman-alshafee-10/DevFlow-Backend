"""
app/api/v1/auth.py
──────────────────
Authentication endpoints (register, login, refresh, logout, etc).
"""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUser, get_auth_service
from app.config import get_settings
from app.schemas.auth import RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.schemas.auth import LoginRequest

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]

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

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, auth_service: AuthServiceDep):
    """Register a new user."""
    return await auth_service.register_user(req)

@router.post("/login", response_model=TokenResponse)
async def login(
    req: Request,
    response: Response,
    auth_service: AuthServiceDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()] = None,
    json_data: LoginRequest = None,
):
    """
    Login to get access and refresh tokens.
    Supports both OAuth2 form data (for Swagger UI) and JSON (for frontend).
    """
    # Extract from whichever was provided
    if form_data:
        email = form_data.username
        password = form_data.password
    elif json_data:
        email = json_data.email
        password = json_data.password
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing login credentials")
        
    login_req = LoginRequest(email=email, password=password)
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
    from fastapi import HTTPException
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
        
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
    """Revoke ALL refresh tokens for the current user."""
    await auth_service.logout_all(current_user.id)
    clear_refresh_token_cookie(response)
    return {"detail": "Logged out of all devices successfully"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get the current authenticated user's profile."""
    return current_user
