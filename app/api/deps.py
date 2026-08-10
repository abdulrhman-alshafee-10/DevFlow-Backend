"""
app/api/deps.py
───────────────
FastAPI dependencies for authentication and database sessions.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio.client import Redis

from app.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.services.auth import AuthService
from app.utils.redis import get_redis_client
from app.utils.security import decode_access_token

# The tokenUrl tells Swagger UI where to send the login request when clicking "Authorize"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

SessionDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis_client)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

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

async def get_current_user(
    token: TokenDep,
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    """
    Dependency that extracts the JWT token from the Authorization header,
    decodes it, and fetches the user from the database.
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
