"""
app/schemas/user.py
───────────────────
Pydantic schemas (DTOs) for the User resource.

Schema types and their purposes:
  UserBase       — shared fields between create and response
  UserCreate     — POST /users request body (includes password)
  UserUpdate     — PATCH /users/{id} body (all fields optional)
  UserResponse   — any endpoint's response (NEVER exposes hashed_password)
  UserDetail     — extended response with all fields (for /users/me, /users/{id})

Design rules:
  1. hashed_password NEVER appears in any response schema
  2. password (plain text) ONLY appears in UserCreate, never stored/returned
  3. UserResponse uses model_config with from_attributes=True so it can be
     built directly from SQLAlchemy model instances
  4. Optional fields in UserUpdate default to None (PatchDoc pattern)
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Base ──────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    """Fields shared between create and response schemas."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)


# ── Request schemas ───────────────────────────────────────────────────────────

class UserCreate(UserBase):
    """
    POST /users request body.

    Password is received in plain text here. The service layer hashes it
    before storing. In Phase 3, hashing moves to the auth service.

    For Phase 2, we store a placeholder hash so the column is populated.
    """
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Basic password rules:
          - At least 8 characters (enforced by Field(min_length=8))
          - At least one letter and one digit

        Phase 3 will add proper strength checking with zxcvbn.
        """
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_letter and has_digit):
            raise ValueError("Password must contain at least one letter and one digit.")
        return v

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Allow letters, digits, underscores, hyphens only."""
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username may only contain letters, digits, underscores, and hyphens."
            )
        return v.lower()


class UserUpdate(BaseModel):
    """
    PATCH /users/{id} request body.

    All fields are optional — clients only send what they want to change.
    This is the standard "partial update" (JSON Patch) pattern.
    """
    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=500)
    # Email and username changes require additional verification steps,
    # so they are handled by dedicated endpoints in Phase 3.


# ── Response schemas ──────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """
    Standard user representation returned by list endpoints and actions.

    from_attributes=True:
      Allows Pydantic to read values directly from SQLAlchemy model attributes
      instead of requiring a plain dict. Enables: UserResponse.model_validate(db_user)
    """
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    is_email_verified: bool
    is_superuser: bool  
    created_at: datetime
    updated_at: datetime

    # hashed_password is intentionally ABSENT — it never leaves the server
