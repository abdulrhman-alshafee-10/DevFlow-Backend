"""
app/models/__init__.py
──────────────────────
Re-exports all models so Alembic can auto-detect them in a single import.

Alembic's env.py does:
    from app.models import *   (or from app.models import Base)

Because Base is imported here alongside all model classes, SQLAlchemy's
metadata object (Base.metadata) has seen every table definition.
"""

from app.models.base import Base, BaseModel  # noqa: F401
from app.models.user import User             # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.organization import (          # noqa: F401
    Organization,
    OrganizationMember,
    Invitation,
    InvitationStatus,
)
from app.models.project import Project, ProjectMember # noqa: F401
from app.models.task import Task # noqa: F401
from app.models.comment import Comment # noqa: F401
from app.models.audit_log import AuditLog # noqa: F401
from app.models.notification import Notification # noqa: F401
from app.models.email_log import EmailLog # noqa: F401
from app.models.attachment import Attachment # noqa: F401
from app.models.ai import AIUsageLog # noqa: F401

__all__ = [
    "Base",
    "BaseModel",
    "User",
    "RefreshToken",
    "Organization",
    "OrganizationMember",
    "Invitation",
    "InvitationStatus",
    "Project",
    "ProjectMember",
    "Task",
    "Comment",
    "AuditLog",
    "Notification",
]
