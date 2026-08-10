"""
app/api/v1/__init__.py
──────────────────────
Aggregates all v1 routers into a single router that main.py mounts.

As new feature routers are added (users, auth, tasks …), import and
include them here. main.py stays unchanged.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router

# The prefix "/api/v1" is added in main.py so individual routers stay clean.
v1_router = APIRouter()

v1_router.include_router(health_router)
