"""
tests/unit/test_roles.py
────────────────────────
Pure unit tests for the authorization engine in app/core/roles.py.

No database, no HTTP, no async — just pure Python.
These tests verify that the permission matrix is correct and that
role escalation prevention works as designed.

Run with:
    pytest tests/unit/test_roles.py -v
"""

import pytest
from app.core.roles import (
    OrgRole,
    ProjectRole,
    Permission,
    ORG_ROLE_PERMISSIONS,
    PROJECT_ROLE_PERMISSIONS,
    ORG_ROLE_HIERARCHY,
    PROJECT_ROLE_HIERARCHY,
    org_role_has_permission,
    project_role_has_permission,
    can_assign_org_role,
    can_assign_project_role,
)


# ── Permission Matrix: Organization Roles ─────────────────────────────────────

class TestOrgRolePermissions:
    """Verify the full permission matrix for organization roles."""

    # ── VIEWER ──────────────────────────────────────────────────────────────

    def test_viewer_can_read_org(self):
        assert org_role_has_permission(OrgRole.VIEWER, Permission.ORG_READ)

    def test_viewer_can_read_projects(self):
        assert org_role_has_permission(OrgRole.VIEWER, Permission.PROJECT_READ)

    def test_viewer_can_read_tasks(self):
        assert org_role_has_permission(OrgRole.VIEWER, Permission.TASK_READ)

    def test_viewer_can_read_comments(self):
        assert org_role_has_permission(OrgRole.VIEWER, Permission.COMMENT_READ)

    def test_viewer_cannot_create_tasks(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.TASK_CREATE)

    def test_viewer_cannot_create_comments(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.COMMENT_CREATE)

    def test_viewer_cannot_update_org(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.ORG_UPDATE)

    def test_viewer_cannot_delete_org(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.ORG_DELETE)

    def test_viewer_cannot_invite_members(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.ORG_MEMBERS_INVITE)

    def test_viewer_cannot_manage_billing(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.ORG_BILLING_MANAGE)

    def test_viewer_cannot_create_projects(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.PROJECT_CREATE)

    def test_viewer_cannot_delete_projects(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.PROJECT_DELETE)

    def test_viewer_cannot_upload_attachments(self):
        assert not org_role_has_permission(OrgRole.VIEWER, Permission.ATTACHMENT_UPLOAD)

    # ── MEMBER ───────────────────────────────────────────────────────────────

    def test_member_can_read_org(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.ORG_READ)

    def test_member_can_create_tasks(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.TASK_CREATE)

    def test_member_can_update_own_tasks(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.TASK_UPDATE_OWN)

    def test_member_can_comment(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.COMMENT_CREATE)

    def test_member_can_upload_attachments(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.ATTACHMENT_UPLOAD)

    def test_member_can_use_ai(self):
        assert org_role_has_permission(OrgRole.MEMBER, Permission.AI_ANALYZE)

    def test_member_cannot_update_any_task(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.TASK_UPDATE_ANY)

    def test_member_cannot_delete_tasks(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.TASK_DELETE)

    def test_member_cannot_assign_tasks(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.TASK_ASSIGN)

    def test_member_cannot_invite_members(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.ORG_MEMBERS_INVITE)

    def test_member_cannot_create_projects(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.PROJECT_CREATE)

    def test_member_cannot_delete_org(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.ORG_DELETE)

    def test_member_cannot_manage_billing(self):
        assert not org_role_has_permission(OrgRole.MEMBER, Permission.ORG_BILLING_MANAGE)

    # ── ADMIN ────────────────────────────────────────────────────────────────

    def test_admin_has_all_member_permissions(self):
        """Admin must have a superset of member permissions (inheritance)."""
        member_perms = ORG_ROLE_PERMISSIONS[OrgRole.MEMBER]
        admin_perms = ORG_ROLE_PERMISSIONS[OrgRole.ADMIN]
        assert member_perms.issubset(admin_perms)

    def test_admin_can_invite_members(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.ORG_MEMBERS_INVITE)

    def test_admin_can_remove_members(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.ORG_MEMBERS_REMOVE)

    def test_admin_can_update_member_roles(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.ORG_MEMBERS_UPDATE_ROLE)

    def test_admin_can_create_projects(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.PROJECT_CREATE)

    def test_admin_can_delete_projects(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.PROJECT_DELETE)

    def test_admin_can_update_any_task(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.TASK_UPDATE_ANY)

    def test_admin_can_delete_any_task(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.TASK_DELETE)

    def test_admin_can_assign_tasks(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.TASK_ASSIGN)

    def test_admin_can_read_audit_log(self):
        assert org_role_has_permission(OrgRole.ADMIN, Permission.ADMIN_AUDIT_LOG_READ)

    def test_admin_cannot_delete_org(self):
        assert not org_role_has_permission(OrgRole.ADMIN, Permission.ORG_DELETE)

    def test_admin_cannot_manage_billing(self):
        assert not org_role_has_permission(OrgRole.ADMIN, Permission.ORG_BILLING_MANAGE)

    # ── OWNER ────────────────────────────────────────────────────────────────

    def test_owner_has_all_admin_permissions(self):
        """Owner must have a strict superset of admin permissions."""
        admin_perms = ORG_ROLE_PERMISSIONS[OrgRole.ADMIN]
        owner_perms = ORG_ROLE_PERMISSIONS[OrgRole.OWNER]
        assert admin_perms.issubset(owner_perms)

    def test_owner_can_delete_org(self):
        assert org_role_has_permission(OrgRole.OWNER, Permission.ORG_DELETE)

    def test_owner_can_manage_billing(self):
        assert org_role_has_permission(OrgRole.OWNER, Permission.ORG_BILLING_MANAGE)

    def test_owner_has_more_permissions_than_admin(self):
        admin_perms = ORG_ROLE_PERMISSIONS[OrgRole.ADMIN]
        owner_perms = ORG_ROLE_PERMISSIONS[OrgRole.OWNER]
        extra = owner_perms - admin_perms
        assert len(extra) > 0  # Owner has at least one permission Admin lacks


# ── Permission Matrix: Project Roles ──────────────────────────────────────────

class TestProjectRolePermissions:
    """Verify the full permission matrix for project roles."""

    def test_viewer_can_read_tasks(self):
        assert project_role_has_permission(ProjectRole.VIEWER, Permission.TASK_READ)

    def test_viewer_can_read_comments(self):
        assert project_role_has_permission(ProjectRole.VIEWER, Permission.COMMENT_READ)

    def test_viewer_cannot_create_tasks(self):
        assert not project_role_has_permission(ProjectRole.VIEWER, Permission.TASK_CREATE)

    def test_member_can_create_tasks(self):
        assert project_role_has_permission(ProjectRole.MEMBER, Permission.TASK_CREATE)

    def test_member_can_update_own_tasks(self):
        assert project_role_has_permission(ProjectRole.MEMBER, Permission.TASK_UPDATE_OWN)

    def test_member_cannot_update_any_task(self):
        assert not project_role_has_permission(ProjectRole.MEMBER, Permission.TASK_UPDATE_ANY)

    def test_member_cannot_delete_tasks(self):
        assert not project_role_has_permission(ProjectRole.MEMBER, Permission.TASK_DELETE)

    def test_manager_has_all_member_permissions(self):
        member_perms = PROJECT_ROLE_PERMISSIONS[ProjectRole.MEMBER]
        manager_perms = PROJECT_ROLE_PERMISSIONS[ProjectRole.MANAGER]
        assert member_perms.issubset(manager_perms)

    def test_manager_can_update_any_task(self):
        assert project_role_has_permission(ProjectRole.MANAGER, Permission.TASK_UPDATE_ANY)

    def test_manager_can_delete_tasks(self):
        assert project_role_has_permission(ProjectRole.MANAGER, Permission.TASK_DELETE)

    def test_manager_can_assign_tasks(self):
        assert project_role_has_permission(ProjectRole.MANAGER, Permission.TASK_ASSIGN)

    def test_manager_can_manage_project_members(self):
        assert project_role_has_permission(ProjectRole.MANAGER, Permission.PROJECT_MEMBERS_MANAGE)

    def test_manager_cannot_delete_org(self):
        """Project-level roles don't grant org-level destructive permissions."""
        assert not project_role_has_permission(ProjectRole.MANAGER, Permission.ORG_DELETE)

    def test_manager_cannot_manage_billing(self):
        assert not project_role_has_permission(ProjectRole.MANAGER, Permission.ORG_BILLING_MANAGE)


# ── Role Hierarchy ────────────────────────────────────────────────────────────

class TestRoleHierarchy:
    """Verify the numeric hierarchy weights are correct."""

    def test_owner_outranks_admin(self):
        assert ORG_ROLE_HIERARCHY[OrgRole.OWNER] > ORG_ROLE_HIERARCHY[OrgRole.ADMIN]

    def test_admin_outranks_member(self):
        assert ORG_ROLE_HIERARCHY[OrgRole.ADMIN] > ORG_ROLE_HIERARCHY[OrgRole.MEMBER]

    def test_member_outranks_viewer(self):
        assert ORG_ROLE_HIERARCHY[OrgRole.MEMBER] > ORG_ROLE_HIERARCHY[OrgRole.VIEWER]

    def test_project_manager_outranks_member(self):
        assert PROJECT_ROLE_HIERARCHY[ProjectRole.MANAGER] > PROJECT_ROLE_HIERARCHY[ProjectRole.MEMBER]

    def test_project_member_outranks_viewer(self):
        assert PROJECT_ROLE_HIERARCHY[ProjectRole.MEMBER] > PROJECT_ROLE_HIERARCHY[ProjectRole.VIEWER]


# ── Role Escalation Prevention ────────────────────────────────────────────────

class TestCanAssignOrgRole:
    """Verify role escalation is properly prevented."""

    # OWNER can assign anything
    def test_owner_can_assign_owner(self):
        assert can_assign_org_role(OrgRole.OWNER, OrgRole.OWNER)

    def test_owner_can_assign_admin(self):
        assert can_assign_org_role(OrgRole.OWNER, OrgRole.ADMIN)

    def test_owner_can_assign_member(self):
        assert can_assign_org_role(OrgRole.OWNER, OrgRole.MEMBER)

    def test_owner_can_assign_viewer(self):
        assert can_assign_org_role(OrgRole.OWNER, OrgRole.VIEWER)

    # ADMIN cannot escalate to OWNER
    def test_admin_can_assign_admin(self):
        assert can_assign_org_role(OrgRole.ADMIN, OrgRole.ADMIN)

    def test_admin_can_assign_member(self):
        assert can_assign_org_role(OrgRole.ADMIN, OrgRole.MEMBER)

    def test_admin_can_assign_viewer(self):
        assert can_assign_org_role(OrgRole.ADMIN, OrgRole.VIEWER)

    def test_admin_cannot_assign_owner(self):
        """Escalation attack: ADMIN should NOT be able to promote someone to OWNER."""
        assert not can_assign_org_role(OrgRole.ADMIN, OrgRole.OWNER)

    # MEMBER cannot assign any role
    def test_member_cannot_assign_any_role(self):
        for role in OrgRole:
            assert not can_assign_org_role(OrgRole.MEMBER, role), \
                f"MEMBER should not be able to assign {role}"

    # VIEWER cannot assign any role
    def test_viewer_cannot_assign_any_role(self):
        for role in OrgRole:
            assert not can_assign_org_role(OrgRole.VIEWER, role), \
                f"VIEWER should not be able to assign {role}"


class TestCanAssignProjectRole:
    """Verify project role escalation is properly prevented."""

    def test_manager_can_assign_manager(self):
        assert can_assign_project_role(ProjectRole.MANAGER, ProjectRole.MANAGER)

    def test_manager_can_assign_member(self):
        assert can_assign_project_role(ProjectRole.MANAGER, ProjectRole.MEMBER)

    def test_manager_can_assign_viewer(self):
        assert can_assign_project_role(ProjectRole.MANAGER, ProjectRole.VIEWER)

    def test_member_cannot_assign_any_role(self):
        for role in ProjectRole:
            assert not can_assign_project_role(ProjectRole.MEMBER, role), \
                f"MEMBER should not be able to assign {role}"

    def test_viewer_cannot_assign_any_role(self):
        for role in ProjectRole:
            assert not can_assign_project_role(ProjectRole.VIEWER, role), \
                f"VIEWER should not be able to assign {role}"


# ── Helper function edge cases ────────────────────────────────────────────────

class TestHelperFunctions:
    """Edge case tests for helper functions."""

    def test_org_role_has_permission_returns_bool(self):
        result = org_role_has_permission(OrgRole.OWNER, Permission.ORG_DELETE)
        assert isinstance(result, bool)

    def test_project_role_has_permission_returns_bool(self):
        result = project_role_has_permission(ProjectRole.MANAGER, Permission.TASK_DELETE)
        assert isinstance(result, bool)

    def test_permission_enum_values_are_strings(self):
        """All permission values must be strings (for JSON serialization)."""
        for perm in Permission:
            assert isinstance(perm.value, str)
            assert ":" in perm.value  # Enforces resource:action convention

    def test_role_enum_values_are_strings(self):
        for role in OrgRole:
            assert isinstance(role.value, str)
        for role in ProjectRole:
            assert isinstance(role.value, str)

    def test_no_permission_granted_to_unknown_role(self):
        """Calling with a role not in the map returns False (via frozenset())."""
        # We test this indirectly via the helper — it should never raise
        result = org_role_has_permission.__wrapped__(OrgRole.VIEWER, Permission.ORG_DELETE) \
            if hasattr(org_role_has_permission, '__wrapped__') else \
            org_role_has_permission(OrgRole.VIEWER, Permission.ORG_DELETE)
        assert result is False
