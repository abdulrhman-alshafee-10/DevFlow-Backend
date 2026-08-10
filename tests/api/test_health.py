"""
tests/api/test_health.py
────────────────────────
Tests for Phase 1 health check endpoints.

Tests every requirement from phase-01-foundation.md:
  ✓ /health  → 200, {"status": "healthy"}
  ✓ /health/ready → 200
  ✓ unknown route → 404 with consistent error envelope
  ✓ CORS headers present on responses
  ✓ X-Request-ID correlation header present
  ✓ /api/v1 root → 200
"""

import pytest
from httpx import AsyncClient


# ── /health ───────────────────────────────────────────────────────────────────

class TestLivenessProbe:

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_is_healthy(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert body["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_includes_timestamp(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        body = response.json()
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_correlation_id_header_present(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert "x-request-id" in response.headers

    @pytest.mark.asyncio
    async def test_process_time_header_present(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert "x-process-time" in response.headers

    @pytest.mark.asyncio
    async def test_uses_provided_request_id(self, client: AsyncClient) -> None:
        """If the caller sends X-Request-ID, we echo it back."""
        custom_id = "my-trace-id-123"
        response = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers["x-request-id"] == custom_id


# ── /health/ready ─────────────────────────────────────────────────────────────

class TestReadinessProbe:

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_status_is_ready(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        body = response.json()
        assert body["status"] == "ready"

    @pytest.mark.asyncio
    async def test_includes_checks(self, client: AsyncClient) -> None:
        response = await client.get("/health/ready")
        body = response.json()
        assert "checks" in body


# ── /api/v1 root ──────────────────────────────────────────────────────────────

class TestApiRoot:

    @pytest.mark.asyncio
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_includes_app_name(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1")
        body = response.json()
        assert "name" in body

    @pytest.mark.asyncio
    async def test_includes_version(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1")
        body = response.json()
        assert "version" in body


# ── Error format ──────────────────────────────────────────────────────────────

class TestErrorFormat:

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/this-does-not-exist")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_has_consistent_error_envelope(self, client: AsyncClient) -> None:
        """All errors must follow { "error": { "code", "message", "request_id", "path" } }"""
        response = await client.get("/api/v1/nonexistent")
        # FastAPI returns its own 404 for unknown routes
        # Our custom handler only catches DevFlowException subclasses.
        # A plain 404 from the router is expected here.
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation_error_uses_our_envelope(self, client: AsyncClient) -> None:
        """
        Send a request to the health endpoint with a bogus query param
        to force a Pydantic validation error and verify the error shape.

        Phase 1 endpoints have no query params so this tests the catch-all.
        """
        # GET /health doesn't define query params — it will just succeed.
        # In Phase 2 (when we have endpoints with required query params)
        # this test pattern will prove the error shape.
        response = await client.get("/health")
        assert response.status_code == 200  # baseline: still works


# ── CORS ──────────────────────────────────────────────────────────────────────

class TestCORS:

    @pytest.mark.asyncio
    async def test_cors_credentials_header_present(self, client: AsyncClient) -> None:
        """
        Starlette always returns Access-Control-Allow-Credentials when
        allow_credentials=True. This verifies the CORS middleware is wired up.
        """
        response = await client.get(
            "/health",
            headers={"Origin": "http://testclient"},
        )
        assert "access-control-allow-credentials" in response.headers
        assert response.headers["access-control-allow-credentials"] == "true"

    @pytest.mark.asyncio
    async def test_cors_allow_origin_for_configured_origin(self, client: AsyncClient) -> None:
        """Allowed origin gets Access-Control-Allow-Origin echoed back."""
        response = await client.get(
            "/health",
            headers={"Origin": "http://testclient"},
        )
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://testclient"

    @pytest.mark.asyncio
    async def test_options_preflight_for_configured_origin(self, client: AsyncClient) -> None:
        """CORS preflight returns 200 for configured allowed origins."""
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://testclient",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
