"""
app/models/refresh_token.py
───────────────────────────
Model for tracking JWT refresh tokens.
"""

from datetime import datetime
import uuid

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """
    Refresh token model to manage session state and token rotation.
    Tokens are hashed in the DB so a leaked DB doesn't give attackers active sessions.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True
    )
    device_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens", lazy="noload")
    replaced_by_token: Mapped["RefreshToken"] = relationship("RefreshToken", remote_side="RefreshToken.id")

    @property
    def is_valid(self) -> bool:
        """Returns True if the token is not revoked and not expired."""
        return self.revoked_at is None and datetime.now(self.expires_at.tzinfo) < self.expires_at
