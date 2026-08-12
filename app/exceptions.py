"""
app/exceptions.py
─────────────────
Custom exception hierarchy for DevFlow.

Design principle:
  - Domain exceptions live here (no HTTP knowledge)
  - The API layer (app/api/error_handlers.py) maps them to HTTP responses
  - Services raise domain exceptions; routers catch them via handlers

Hierarchy:
  DevFlowException (base)
  ├── NotFoundError
  ├── AuthenticationError
  │   ├── InvalidCredentialsError
  │   ├── TokenExpiredError
  │   └── InvalidTokenError
  ├── AuthorizationError
  │   └── InsufficientPermissionsError
  ├── ConflictError
  │   └── AlreadyExistsError
  ├── ValidationError
  └── RateLimitError
"""


class DevFlowException(Exception):
    """
    Base exception for all application-level errors.

    Always include a human-readable message and an optional machine-readable
    error_code so clients can react programmatically.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred.",
        error_code: str = "INTERNAL_ERROR",
    ) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, error_code={self.error_code!r})"


# ── Not Found ─────────────────────────────────────────────────────────────────

class NotFoundError(DevFlowException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "The requested resource was not found.",
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(message, error_code)


# ── Authentication ────────────────────────────────────────────────────────────

class AuthenticationError(DevFlowException):
    """Base class for authentication failures."""

    def __init__(
        self,
        message: str = "Authentication failed.",
        error_code: str = "AUTHENTICATION_ERROR",
    ) -> None:
        super().__init__(message, error_code)


class InvalidCredentialsError(AuthenticationError):
    """Wrong email or password."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password.",
            error_code="INVALID_CREDENTIALS",
        )


class TokenExpiredError(AuthenticationError):
    """JWT or refresh token has expired."""

    def __init__(self) -> None:
        super().__init__(
            message="Your session has expired. Please log in again.",
            error_code="TOKEN_EXPIRED",
        )


class InvalidTokenError(AuthenticationError):
    """Token is malformed, revoked, or otherwise invalid."""

    def __init__(self, message: str = "Invalid or revoked token.") -> None:
        super().__init__(message=message, error_code="INVALID_TOKEN")


# ── Authorization ─────────────────────────────────────────────────────────────

class AuthorizationError(DevFlowException):
    """Base class for authorization failures."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        error_code: str = "AUTHORIZATION_ERROR",
    ) -> None:
        super().__init__(message, error_code)


class InsufficientPermissionsError(AuthorizationError):
    """User is authenticated but lacks the required permission."""

    def __init__(self, required_permission: str = "") -> None:
        detail = (
            f"Required permission: {required_permission}."
            if required_permission
            else "Insufficient permissions."
        )
        super().__init__(message=detail, error_code="INSUFFICIENT_PERMISSIONS")


# ── Conflict ──────────────────────────────────────────────────────────────────

class ConflictError(DevFlowException):
    """Raised when an operation would create a conflicting state."""

    def __init__(
        self,
        message: str = "A conflict occurred.",
        error_code: str = "CONFLICT",
    ) -> None:
        super().__init__(message, error_code)


class AlreadyExistsError(ConflictError):
    """A unique resource already exists (e.g. duplicate email)."""

    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(
            message=f"{resource} already exists.",
            error_code="ALREADY_EXISTS",
        )


# ── Validation ────────────────────────────────────────────────────────────────

class BusinessRuleError(DevFlowException):
    """A business rule was violated (not a schema validation error)."""

    def __init__(
        self,
        message: str = "A business rule was violated.",
        error_code: str = "BUSINESS_RULE_VIOLATION",
    ) -> None:
        super().__init__(message, error_code)


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class RateLimitError(DevFlowException):
    """Client has exceeded the allowed request rate."""

    def __init__(self, retry_after: int = 60, limit: int = 0, remaining: int = 0, reset: int = 0) -> None:
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.reset = reset
        super().__init__(
            message=f"Too many requests. Please retry after {retry_after} seconds.",
            error_code="RATE_LIMIT_EXCEEDED",
        )
