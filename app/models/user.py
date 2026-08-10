"""
app/models/user.py
──────────────────
User model — the central entity in DevFlow.

Every other entity (tasks, projects, comments) relates back to users.
This model is intentionally minimal in Phase 2; fields for OAuth, 2FA, etc.
are added in later phases when they are actually needed.

Security notes:
  - hashed_password stores the bcrypt hash, NEVER the plain text
  - is_email_verified prevents login-gated features until email is confirmed
  - is_active allows soft-disabling an account without deleting it
  - is_superuser is a flag for system-level admin (not organization admin)
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Security ──────────────────────────────────────────────────────────────
    # Phase 3 (Authentication) will add the bcrypt hashing logic.
    # We define the column here so the schema is complete from the start.
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # ── Status flags ──────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
