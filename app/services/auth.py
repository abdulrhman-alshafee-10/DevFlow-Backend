"""
app/services/auth.py
────────────────────
Authentication and authorization service logic.
"""

from datetime import datetime, timedelta, timezone
import secrets
import hashlib
from uuid import UUID

from fastapi import HTTPException, status
from redis.asyncio.client import Redis

from app.config import get_settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories.user import UserRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.schemas.auth import RegisterRequest, TokenResponse, LoginRequest
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.utils.email import send_email

settings = get_settings()

class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
        redis_client: Redis,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.redis_client = redis_client

    async def _check_brute_force(self, email: str, ip_address: str | None = None) -> None:
        """Checks and increments failed login attempts."""
        email_key = f"login_attempts:email:{email}"
        attempts = await self.redis_client.incr(email_key)
        if attempts == 1:
            await self.redis_client.expire(email_key, 15 * 60) # 15 mins
            
        if attempts > 5:
            # Let's say we lock it for 15 mins
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Try again later."
            )

    async def _clear_brute_force(self, email: str) -> None:
        await self.redis_client.delete(f"login_attempts:email:{email}")

    async def register_user(self, req: RegisterRequest) -> User:
        if await self.user_repo.email_exists(req.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        if await self.user_repo.username_exists(req.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken"
            )

        user = await self.user_repo.create(
            email=req.email.lower(),
            username=req.username.lower(),
            hashed_password=get_password_hash(req.password),
            full_name=req.full_name
        )
        
        # In a real app, send verification email here
        await send_email(
            email_to=user.email,
            subject="Welcome to DevFlow - Verify Email",
            body="Please verify your email."
        )
        
        return user

    def _hash_token(self, token: str) -> str:
        """Hashes the refresh token using SHA-256."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def login(
        self,
        req: LoginRequest,
        device_info: str | None = None,
        ip_address: str | None = None
    ) -> tuple[str, str]:
        """Returns (access_token, raw_refresh_token)."""
        await self._check_brute_force(req.email, ip_address)
        
        user = await self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        await self._clear_brute_force(req.email)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
            )

        # Create access token
        access_token = create_access_token(subject=user.id)
        
        # Create refresh token
        raw_refresh_token = secrets.token_urlsafe(32)
        hashed_token = self._hash_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        await self.token_repo.create(
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )
        
        return access_token, raw_refresh_token

    async def refresh_tokens(self, raw_refresh_token: str) -> tuple[str, str]:
        """Handles refresh token rotation and reuse detection."""
        hashed_token = self._hash_token(raw_refresh_token)
        db_token = await self.token_repo.get_by_token_hash(hashed_token)
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        # Reuse detection
        if db_token.revoked_at is not None:
            # Token was already used/revoked, but someone tried to use it again!
            # Revoke ALL tokens for this user as a security measure.
            await self.token_repo.revoke_all_for_user(db_token.user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token reuse detected. All sessions revoked."
            )

        if not db_token.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
            )

        # Mark old token as revoked (rotated)
        db_token.revoked_at = datetime.now(timezone.utc)
        
        # Create new tokens
        new_access_token = create_access_token(subject=db_token.user_id)
        new_raw_refresh_token = secrets.token_urlsafe(32)
        new_hashed_token = self._hash_token(new_raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        new_db_token = await self.token_repo.create(
            user_id=db_token.user_id,
            token_hash=new_hashed_token,
            expires_at=expires_at,
            device_info=db_token.device_info,
            ip_address=db_token.ip_address
        )
        
        db_token.replaced_by = new_db_token.id
        await self.token_repo.update(db_token)
        
        return new_access_token, new_raw_refresh_token

    async def logout(self, raw_refresh_token: str) -> None:
        """Revokes a single refresh token."""
        hashed_token = self._hash_token(raw_refresh_token)
        db_token = await self.token_repo.get_by_token_hash(hashed_token)
        if db_token and db_token.revoked_at is None:
            db_token.revoked_at = datetime.now(timezone.utc)
            await self.token_repo.update(db_token)

    async def logout_all(self, user_id: UUID) -> None:
        """Revokes all refresh tokens for a user."""
        await self.token_repo.revoke_all_for_user(user_id)
