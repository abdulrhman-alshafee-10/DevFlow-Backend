"""
app/api/error_handlers.py
─────────────────────────
Global exception handlers.

Maps domain exceptions (from app/exceptions.py) and FastAPI exceptions
to a single, consistent JSON error envelope:

  {
    "error": {
      "code":       "NOT_FOUND",
      "message":    "The requested resource was not found.",
      "request_id": "abc-123",
      "path":       "/api/v1/tasks/999"
    }
  }

Clients always get the same shape — they only need to handle one format.
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    DevFlowException,
    NotFoundError,
    RateLimitError,
)
from app.middleware.logging import request_id_ctx_var


def _error_body(code: str, message: str, request: Request) -> dict:
    """Build the standard error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_ctx_var.get() or "unknown",
            "path": str(request.url.path),
        }
    }


# ── Domain exceptions → HTTP ──────────────────────────────────────────────────

async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=_error_body(exc.error_code, exc.message, request),
    )


async def authentication_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=_error_body(exc.error_code, exc.message, request),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def authorization_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=_error_body(exc.error_code, exc.message, request),
    )


async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=_error_body(exc.error_code, exc.message, request),
    )


async def business_rule_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_body(exc.error_code, exc.message, request),
    )


async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)}
    if exc.limit:
        headers["X-RateLimit-Limit"] = str(exc.limit)
    if exc.reset:
        headers["X-RateLimit-Remaining"] = str(exc.remaining)
        headers["X-RateLimit-Reset"] = str(exc.reset)
        
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=_error_body(exc.error_code, exc.message, request),
        headers=headers,
    )


async def devflow_exception_handler(request: Request, exc: DevFlowException) -> JSONResponse:
    """Catch-all for any DevFlowException that isn't handled above."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(exc.error_code, exc.message, request),
    )


# ── FastAPI / Pydantic errors ─────────────────────────────────────────────────

async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Reformat Pydantic's default validation errors into our envelope.

    The default FastAPI format is { "detail": [...] } which doesn't match
    our { "error": { ... } } shape.
    """
    # Collect the first few validation errors in a readable format
    errors = [
        {
            "field": " → ".join(str(loc) for loc in err["loc"]),
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "request_id": request_id_ctx_var.get() or "unknown",
                "path": str(request.url.path),
                "details": errors,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Last-resort handler for any unhandled exception.

    NEVER expose internal details (stack trace, SQL errors) to the client.
    Log them here; return a generic 500.
    """
    # TODO (Phase 17): Replace print with structured logger
    print(f"[UNHANDLED] {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_body(
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred. Please try again later.",
            request,
        ),
    )
