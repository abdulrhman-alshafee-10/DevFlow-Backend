"""
app/api/v1/__init__.py
──────────────────────
Aggregates all v1 routers into a single router that main.py mounts.

As new feature routers are added (users, auth, tasks …), import and
include them here. main.py stays unchanged.
"""

from fastapi import APIRouter, Depends

from app.core.rate_limit import RateLimiter

from app.api.v1.health import router as health_router
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import org_router, inv_router
from app.api.v1.projects import org_project_router, project_router
from app.api.v1.tasks import router as task_router
from app.api.v1.comments import router as comment_router
from app.api.v1.notifications import router as notification_router
from app.api.v1.endpoints.attachments import router as attachment_router
from app.api.v1.endpoints.search import router as search_router

# The prefix "/api/v1" is added in main.py so individual routers stay clean.
v1_router = APIRouter()

general_rate_limit = [Depends(RateLimiter(limit=100, window=60, tier="general"))]

v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(users_router, dependencies=general_rate_limit)
v1_router.include_router(org_router, dependencies=general_rate_limit)
v1_router.include_router(inv_router, dependencies=general_rate_limit)
v1_router.include_router(org_project_router, dependencies=general_rate_limit)
v1_router.include_router(project_router, dependencies=general_rate_limit)
v1_router.include_router(task_router, dependencies=general_rate_limit)
v1_router.include_router(comment_router, dependencies=general_rate_limit)
v1_router.include_router(notification_router, prefix="/notifications", tags=["notifications"], dependencies=general_rate_limit)
v1_router.include_router(attachment_router, tags=["attachments"], dependencies=general_rate_limit)
v1_router.include_router(search_router, prefix="/search", tags=["search"], dependencies=general_rate_limit)
