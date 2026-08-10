"""
app/main.py
───────────
FastAPI application factory.

The application is built with a factory function (create_app) rather than
creating a global `app` object at module level. This is a best practice for:
  - Testing: each test can call create_app() for a fresh, isolated instance
  - Flexibility: different configurations for dev/prod without code changes
  - Clarity: everything the app needs to start is in one place

Entry points:
  Development:  uvicorn app.main:app --reload
  Production:   gunicorn -k uvicorn.workers.UvicornWorker app.main:app
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import (
    authentication_handler,
    authorization_handler,
    business_rule_handler,
    conflict_handler,
    devflow_exception_handler,
    not_found_handler,
    rate_limit_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.api.v1 import v1_router
from app.config import Settings, get_settings
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
from app.middleware.logging import RequestLoggingMiddleware


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Code BEFORE yield  → runs at startup
    Code AFTER  yield  → runs at shutdown (even on errors)

    Phase 1: No external resources yet — just a startup log.
    Phase 2: Database engine initialization goes here.
    Phase 3: Redis connection goes here.
    Phase 9: WebSocket connection manager goes here.
    """
    settings: Settings = app.state.settings  # type: ignore[attr-defined]

    # ── Startup ───────────────────────────────────────────────────────────────
    print(
        f"🚀  {settings.APP_NAME} v{settings.APP_VERSION} starting "
        f"[env={settings.ENVIRONMENT}]"
    )

    # TODO (Phase 2): await init_database(settings)
    # TODO (Phase 3): await init_redis(settings)

    yield  # ← Application is now running and handling requests

    # ── Shutdown ──────────────────────────────────────────────────────────────
    print(f"🛑  {settings.APP_NAME} shutting down…")

    # TODO (Phase 2): await close_database()
    # TODO (Phase 3): await close_redis()


# ── Factory ───────────────────────────────────────────────────────────────────

def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Build and return a configured FastAPI application.

    Parameters
    ----------
    settings:
        Optional Settings override. Defaults to the cached get_settings().
        Pass a custom Settings in tests to avoid touching the real .env file.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        # Disable docs in production (see config.py)
        openapi_url=settings.openapi_url,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        lifespan=lifespan,
    )

    # Make settings available anywhere via request.app.state.settings
    app.state.settings = settings

    # ── Middleware ────────────────────────────────────────────────────────────
    # Order matters: middleware wraps in reverse registration order.
    # Outer → Inner: CORS → Logging → endpoint

    # 1. CORS — must be first so OPTIONS pre-flight requests are handled
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,         # needed for HttpOnly refresh token cookies
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # 2. Request logging with correlation IDs
    app.add_middleware(RequestLoggingMiddleware)

    # ── Exception Handlers ────────────────────────────────────────────────────
    # Registration order doesn't affect dispatch; the most specific exception
    # class is matched first automatically.

    app.add_exception_handler(NotFoundError, not_found_handler)           # type: ignore[arg-type]
    app.add_exception_handler(AuthenticationError, authentication_handler)# type: ignore[arg-type]
    app.add_exception_handler(AuthorizationError, authorization_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ConflictError, conflict_handler)            # type: ignore[arg-type]
    app.add_exception_handler(BusinessRuleError, business_rule_handler)   # type: ignore[arg-type]
    app.add_exception_handler(RateLimitError, rate_limit_handler)         # type: ignore[arg-type]
    app.add_exception_handler(DevFlowException, devflow_exception_handler)# type: ignore[arg-type]

    # FastAPI / Pydantic errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]

    # Catch-all for truly unexpected exceptions
    app.add_exception_handler(Exception, unhandled_exception_handler)     # type: ignore[arg-type]

    # ── Routers ───────────────────────────────────────────────────────────────
    # /health and /health/ready are at the root (no /api/v1 prefix) so that
    # load balancers and monitoring tools can reach them easily.
    # The health router is also included inside v1_router for API completeness.
    from app.api.v1.health import router as health_router

    app.include_router(health_router)               # bare: /health, /health/ready
    app.include_router(v1_router, prefix="/api/v1") # versioned: /api/v1/health

    # ── Root endpoint ─────────────────────────────────────────────────────────
    @app.get("/api/v1", tags=["meta"], summary="API root")
    async def api_root() -> dict:
        """
        API entry point.

        Returns basic information about the API version and available resources.
        Useful for client auto-discovery.
        """
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs": settings.docs_url,
        }

    return app


# ── Application instance ──────────────────────────────────────────────────────
# Created once when the module is imported. Uvicorn references this object.
app = create_app()
