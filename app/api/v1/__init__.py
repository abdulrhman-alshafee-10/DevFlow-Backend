"""
app/api/v1/__init__.py
──────────────────────
Aggregates all v1 routers into a single router that main.py mounts.

As new feature routers are added (users, auth, tasks …), import and
include them here. main.py stays unchanged.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import org_router, inv_router
from app.api.v1.projects import org_project_router, project_router
from app.api.v1.tasks import router as task_router
from app.api.v1.comments import router as comment_router

# The prefix "/api/v1" is added in main.py so individual routers stay clean.
v1_router = APIRouter()

v1_router.include_router(health_router)
v1_router.include_router(users_router)
v1_router.include_router(auth_router)
v1_router.include_router(org_router)
v1_router.include_router(inv_router)
v1_router.include_router(org_project_router)
v1_router.include_router(project_router)
v1_router.include_router(task_router)
v1_router.include_router(comment_router)
