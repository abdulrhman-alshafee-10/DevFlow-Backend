"""
app/schemas/common.py
─────────────────────
Shared Pydantic schemas used across the entire application.

  PaginatedResponse[T] — Generic paginated list response
  ErrorDetail          — Single validation error item
  ErrorResponse        — The standard error envelope

Why a generic PaginatedResponse?
  Using Python generics (PaginatedResponse[UserResponse]) means:
  - FastAPI generates the correct OpenAPI schema per resource type
  - Type checkers know the exact shape of `items`
  - One definition covers all paginated endpoints (tasks, projects, users, etc.)
"""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Reusable query parameter model for paginated endpoints.

    FastAPI will automatically parse these from query strings:
      GET /users?page=2&size=20
    """
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def offset(self) -> int:
        """Convert page/size to SQL OFFSET."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated list response.

    Example:
      GET /api/v1/users?page=2&size=20
      → PaginatedResponse[UserResponse](
            items=[...],
            total=150,
            page=2,
            size=20,
            pages=8,
            has_next=True,
            has_prev=True,
        )
    """
    items: list[T]
    total: int = Field(description="Total number of items across all pages")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool
    has_prev: bool

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        """Convenience constructor that computes derived fields."""
        pages = math.ceil(total / size) if total > 0 else 1
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )
