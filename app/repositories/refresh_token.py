"""
app/repositories/refresh_token.py
─────────────────────────────────
Repository for RefreshToken operations.
"""

from typing import Sequence
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository

class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Find a refresh token by its hashed value."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: uuid.UUID) -> Sequence[RefreshToken]:
        """Get all refresh tokens for a user."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        return result.scalars().all()

    async def revoke_all_for_user(self, user_id: uuid.UUID, revoked_at: str | None = None) -> None:
        """Revokes all active refresh tokens for a user (e.g., when password changes)."""
        from datetime import datetime, timezone
        if revoked_at is None:
            revoked_at = datetime.now(timezone.utc)
            
        tokens = await self.get_all_for_user(user_id)
        for token in tokens:
            if token.revoked_at is None:
                token.revoked_at = revoked_at
        
        await self.session.flush()
