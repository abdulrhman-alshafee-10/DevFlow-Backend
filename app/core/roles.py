"""
app/core/roles.py
─────────────────
The single source of truth for all role and permission logic in DevFlow.

Architecture:
  - OrgRole     → roles a user holds within an Organization
  - ProjectRole → roles a user holds within a Project
  - Permission  → granular action strings (e.g. "task:create")
  - ORG_ROLE_PERMISSIONS     → maps OrgRole → frozenset[Permission]
  - PROJECT_ROLE_PERMISSIONS → maps ProjectRole → frozenset[Permission]
  - ROLE_HIERARCHY           → numeric weight for escalation prevention

Role Hierarchy (Organization):
  OWNER  (4) → Full control: billing, delete org, manage all members
    ↓
  ADMIN  (3) → Manage members, projects, settings
    ↓
  MEMBER (2) → Create/edit own tasks, comment, upload files
    ↓
  VIEWER (1) → Read-only access to projects and tasks

Role Hierarchy (Project):
  MANAGER (3) → Manage tasks, assign work, manage project members
    ↓
  MEMBER  (2) → Create/edit own tasks, comment, upload files
    ↓
  VIEWER  (1) → Read-only

Usage:
    from app.core.roles import OrgRole, Permission, org_role_has_permission

    if org_role_has_permission(OrgRole.ADMIN, Permission.PROJECT_CREATE):
        ...  # allowed
"""

from enum import Enum


# ── Role Enums ────────────────────────────────────────────────────────────────

class OrgRole(str, Enum):
    """Roles a user can hold within an Organization."""
    OWNER  = "owner"
    ADMIN  = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class ProjectRole(str, Enum):
    """Roles a user can hold within a Project."""
    MANAGER = "manager"
    MEMBER  = "member"
    VIEWER  = "viewer"


# ── Permission Catalog ────────────────────────────────────────────────────────

class Permission(str, Enum):
    """
    Every granular permission in the system.

    Convention: <resource>:<action>
    Use *_ANY for operations that apply to any resource instance (e.g. edit any task).
    Use *_OWN for operations that apply only to resources the user owns.
    """

    # ── Organization ─────────────────────────────────────────────────────────
    ORG_READ               = "org:read"
    ORG_UPDATE             = "org:update"
    ORG_DELETE             = "org:delete"

    ORG_MEMBERS_READ        = "org:members:read"
    ORG_MEMBERS_INVITE      = "org:members:invite"
    ORG_MEMBERS_REMOVE      = "org:members:remove"
    ORG_MEMBERS_UPDATE_ROLE = "org:members:update_role"

    ORG_BILLING_MANAGE     = "org:billing:manage"

    # ── Project ───────────────────────────────────────────────────────────────
    PROJECT_CREATE         = "project:create"
    PROJECT_READ           = "project:read"
    PROJECT_UPDATE         = "project:update"
    PROJECT_DELETE         = "project:delete"
    PROJECT_MEMBERS_MANAGE = "project:members:manage"

    # ── Task ──────────────────────────────────────────────────────────────────
    TASK_CREATE            = "task:create"
    TASK_READ              = "task:read"
    TASK_UPDATE_ANY        = "task:update:any"   # edit any task in the project
    TASK_UPDATE_OWN        = "task:update:own"   # edit only tasks you created
    TASK_DELETE            = "task:delete"
    TASK_ASSIGN            = "task:assign"

    # ── Comment ───────────────────────────────────────────────────────────────
    COMMENT_CREATE         = "comment:create"
    COMMENT_READ           = "comment:read"
    COMMENT_UPDATE_OWN     = "comment:update:own"
    COMMENT_DELETE_ANY     = "comment:delete:any"

    # ── Attachment ────────────────────────────────────────────────────────────
    ATTACHMENT_UPLOAD      = "attachment:upload"
    ATTACHMENT_READ        = "attachment:read"
    ATTACHMENT_DELETE      = "attachment:delete"

    # ── Notification ──────────────────────────────────────────────────────────
    NOTIFICATION_READ      = "notification:read"
    NOTIFICATION_UPDATE    = "notification:update"

    # ── AI ────────────────────────────────────────────────────────────────────
    AI_ANALYZE             = "ai:analyze"
    AI_SUGGEST             = "ai:suggest"

    # ── Admin (system-level) ──────────────────────────────────────────────────
    ADMIN_AUDIT_LOG_READ   = "admin:audit_log:read"


# ── Role → Permission Matrices ────────────────────────────────────────────────

# Shorthand for readability
_P = Permission

# ── Viewer permissions (read-only baseline) ───────────────────────────────────
_VIEWER_ORG_PERMS: frozenset[Permission] = frozenset({
    _P.ORG_READ,
    _P.ORG_MEMBERS_READ,
    _P.PROJECT_READ,
    _P.TASK_READ,
    _P.COMMENT_READ,
    _P.ATTACHMENT_READ,
    _P.NOTIFICATION_READ,
    _P.NOTIFICATION_UPDATE,
})

# ── Member permissions (viewer + write operations on own resources) ────────────
_MEMBER_ORG_PERMS: frozenset[Permission] = _VIEWER_ORG_PERMS | frozenset({
    _P.TASK_CREATE,
    _P.TASK_UPDATE_OWN,
    _P.COMMENT_CREATE,
    _P.COMMENT_UPDATE_OWN,
    _P.ATTACHMENT_UPLOAD,
    _P.AI_ANALYZE,
    _P.AI_SUGGEST,
})

# ── Admin permissions (member + manage members, projects, any task) ─────────
_ADMIN_ORG_PERMS: frozenset[Permission] = _MEMBER_ORG_PERMS | frozenset({
    _P.ORG_UPDATE,
    _P.ORG_MEMBERS_INVITE,
    _P.ORG_MEMBERS_REMOVE,
    _P.ORG_MEMBERS_UPDATE_ROLE,
    _P.PROJECT_CREATE,
    _P.PROJECT_UPDATE,
    _P.PROJECT_DELETE,
    _P.PROJECT_MEMBERS_MANAGE,
    _P.TASK_UPDATE_ANY,
    _P.TASK_DELETE,
    _P.TASK_ASSIGN,
    _P.COMMENT_DELETE_ANY,
    _P.ATTACHMENT_DELETE,
    _P.ADMIN_AUDIT_LOG_READ,
})

# ── Owner permissions (admin + delete org + billing) ─────────────────────────
_OWNER_ORG_PERMS: frozenset[Permission] = _ADMIN_ORG_PERMS | frozenset({
    _P.ORG_DELETE,
    _P.ORG_BILLING_MANAGE,
})


ORG_ROLE_PERMISSIONS: dict[OrgRole, frozenset[Permission]] = {
    OrgRole.OWNER:  _OWNER_ORG_PERMS,
    OrgRole.ADMIN:  _ADMIN_ORG_PERMS,
    OrgRole.MEMBER: _MEMBER_ORG_PERMS,
    OrgRole.VIEWER: _VIEWER_ORG_PERMS,
}


# ── Project-level permission matrices ─────────────────────────────────────────

_VIEWER_PROJECT_PERMS: frozenset[Permission] = frozenset({
    _P.PROJECT_READ,
    _P.TASK_READ,
    _P.COMMENT_READ,
    _P.ATTACHMENT_READ,
    _P.NOTIFICATION_READ,
    _P.NOTIFICATION_UPDATE,
})

_MEMBER_PROJECT_PERMS: frozenset[Permission] = _VIEWER_PROJECT_PERMS | frozenset({
    _P.TASK_CREATE,
    _P.TASK_UPDATE_OWN,
    _P.COMMENT_CREATE,
    _P.COMMENT_UPDATE_OWN,
    _P.ATTACHMENT_UPLOAD,
    _P.AI_ANALYZE,
    _P.AI_SUGGEST,
})

_MANAGER_PROJECT_PERMS: frozenset[Permission] = _MEMBER_PROJECT_PERMS | frozenset({
    _P.PROJECT_UPDATE,
    _P.PROJECT_MEMBERS_MANAGE,
    _P.TASK_UPDATE_ANY,
    _P.TASK_DELETE,
    _P.TASK_ASSIGN,
    _P.COMMENT_DELETE_ANY,
    _P.ATTACHMENT_DELETE,
})


PROJECT_ROLE_PERMISSIONS: dict[ProjectRole, frozenset[Permission]] = {
    ProjectRole.MANAGER: _MANAGER_PROJECT_PERMS,
    ProjectRole.MEMBER:  _MEMBER_PROJECT_PERMS,
    ProjectRole.VIEWER:  _VIEWER_PROJECT_PERMS,
}


# ── Role Hierarchy (for escalation prevention) ────────────────────────────────

# Higher number = more privilege. A user can only assign roles ≤ their own weight.
ORG_ROLE_HIERARCHY: dict[OrgRole, int] = {
    OrgRole.OWNER:  4,
    OrgRole.ADMIN:  3,
    OrgRole.MEMBER: 2,
    OrgRole.VIEWER: 1,
}

PROJECT_ROLE_HIERARCHY: dict[ProjectRole, int] = {
    ProjectRole.MANAGER: 3,
    ProjectRole.MEMBER:  2,
    ProjectRole.VIEWER:  1,
}


# ── Helper Functions ──────────────────────────────────────────────────────────

def org_role_has_permission(role: OrgRole, permission: Permission) -> bool:
    """
    Return True if the given OrgRole grants the specified Permission.

    Example:
        org_role_has_permission(OrgRole.ADMIN, Permission.PROJECT_CREATE)  # True
        org_role_has_permission(OrgRole.VIEWER, Permission.TASK_CREATE)    # False
    """
    return permission in ORG_ROLE_PERMISSIONS.get(role, frozenset())


def project_role_has_permission(role: ProjectRole, permission: Permission) -> bool:
    """
    Return True if the given ProjectRole grants the specified Permission.

    Example:
        project_role_has_permission(ProjectRole.MANAGER, Permission.TASK_DELETE)  # True
        project_role_has_permission(ProjectRole.VIEWER, Permission.TASK_CREATE)   # False
    """
    return permission in PROJECT_ROLE_PERMISSIONS.get(role, frozenset())


def can_assign_org_role(assigner_role: OrgRole, target_role: OrgRole) -> bool:
    """
    Return True if a user with `assigner_role` is allowed to assign `target_role`
    to another user. Prevents privilege escalation.

    Rules:
      - OWNER can assign any role (including OWNER).
      - ADMIN can assign ADMIN, MEMBER, VIEWER — but NOT OWNER.
      - MEMBER and VIEWER cannot assign any role.

    Example:
        can_assign_org_role(OrgRole.ADMIN, OrgRole.MEMBER)  # True
        can_assign_org_role(OrgRole.ADMIN, OrgRole.OWNER)   # False (escalation!)
        can_assign_org_role(OrgRole.MEMBER, OrgRole.VIEWER) # False (no permission)
    """
    assigner_weight = ORG_ROLE_HIERARCHY.get(assigner_role, 0)
    target_weight   = ORG_ROLE_HIERARCHY.get(target_role, 0)

    # Must have at least ADMIN level to assign any role
    if assigner_weight < ORG_ROLE_HIERARCHY[OrgRole.ADMIN]:
        return False

    # Cannot assign a role higher than your own
    return target_weight <= assigner_weight


def can_assign_project_role(assigner_role: ProjectRole, target_role: ProjectRole) -> bool:
    """
    Return True if a user with `assigner_role` can assign `target_role` within a project.

    Rules:
      - MANAGER can assign MANAGER, MEMBER, VIEWER.
      - MEMBER and VIEWER cannot assign any role.

    Example:
        can_assign_project_role(ProjectRole.MANAGER, ProjectRole.MEMBER)  # True
        can_assign_project_role(ProjectRole.MEMBER, ProjectRole.VIEWER)   # False
    """
    assigner_weight = PROJECT_ROLE_HIERARCHY.get(assigner_role, 0)
    target_weight   = PROJECT_ROLE_HIERARCHY.get(target_role, 0)

    if assigner_weight < PROJECT_ROLE_HIERARCHY[ProjectRole.MANAGER]:
        return False

    return target_weight <= assigner_weight
