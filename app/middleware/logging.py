"""
app/middleware/logging.py
─────────────────────────
Request/response logging middleware with correlation IDs.

What it does on every request:
  1. Reads or generates a unique X-Request-ID header (correlation ID)
  2. Stores it in a contextvars.ContextVar so any logger can access it
  3. Logs the incoming request (method, path)
  4. Calls the next handler
  5. Logs the completed response (method, path, status, duration)
  6. Attaches X-Request-ID and X-Process-Time to the response headers

Why correlation IDs?
  When something goes wrong you can grep logs for the request ID and see
  the full picture — even across microservices or background tasks.
"""

import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ── Context variable ──────────────────────────────────────────────────────────
# Other parts of the app can read the current request ID with:
#   from app.middleware.logging import request_id_ctx_var
#   current_id = request_id_ctx_var.get()
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that logs every HTTP request/response.

    Uses plain print() for Phase 1 so there are zero extra dependencies.
    Phase 17 (Observability) will swap this for structlog JSON logging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # ── 1. Correlation ID ─────────────────────────────────────────────────
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx_var.set(request_id)

        # ── 2. Log incoming request ───────────────────────────────────────────
        start_time = time.perf_counter()
        print(
            f"[{request_id}] → {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        # ── 3. Process request ────────────────────────────────────────────────
        try:
            response = await call_next(request)
        except Exception:
            # Let FastAPI exception handlers deal with it;
            # we still want the log line.
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            request_id_ctx_var.reset(token)

        # ── 4. Log response ───────────────────────────────────────────────────
        print(
            f"[{request_id}] ← {request.method} {request.url.path} "
            f"| status={response.status_code} | {duration_ms:.1f}ms"
        )

        # ── 5. Attach headers so callers can trace requests ───────────────────
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms:.1f}ms"

        return response
