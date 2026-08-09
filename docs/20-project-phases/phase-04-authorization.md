# Phase 4 — Authorization

## Objective

Implement Role-Based Access Control (RBAC) with a permission system. Define roles (OWNER, ADMIN, MANAGER, MEMBER, VIEWER) and map them to granular permissions. Create authorization dependencies that protect endpoints based on the user's role and resource access.

---

## Concepts Learned

- Role-Based Access Control (RBAC)
- Permission mapping and checking
- Resource-level authorization
- Authorization as FastAPI dependencies
- Role hierarchy and inheritance
- Preventing role escalation

**Relevant docs**:
- `05-authorization/` (all files)

---

## Features After This Phase

- [ ] Role enum (OWNER, ADMIN, MANAGER, MEMBER, VIEWER)
- [ ] Permission catalog (granular action-based permissions)
- [ ] Role-to-permission mapping
- [ ] `require_permission()` dependency
- [ ] Role escalation prevention
- [ ] Authorization checks on all existing endpoints

> **Note**: Roles are fully applied starting in Phase 5 (Organizations) when membership is created. This phase establishes the framework.

---

## Database Changes

No new tables yet — the authorization framework is code-only. Organization and project membership tables (which carry the role) are created in Phases 5 and 6.

### Constants / Enums

```python
# Roles
class OrgRole: OWNER, ADMIN, MEMBER, VIEWER
class ProjectRole: MANAGER, MEMBER, VIEWER

# Permission catalog
PERMISSION_MAP = {
    OrgRole.OWNER: {"org:*", "project:*", "task:*", ...},
    OrgRole.ADMIN: {"org:read", "org:update", "org:members:*", "project:*", ...},
    OrgRole.MEMBER: {"org:read", "project:read", "task:create", "task:read", ...},
    OrgRole.VIEWER: {"org:read", "project:read", "task:read"},
}
```

---

## API Endpoints

No new endpoints in this phase. Authorization dependencies are added to existing endpoints.

---

## Testing Requirements

- Permission mapping is correct for each role
- `require_permission()` allows valid roles
- `require_permission()` denies invalid roles with 403
- Unauthenticated requests return 401 (not 403)
- Role escalation is prevented (MEMBER can't assign ADMIN role)

---

## Completion Checklist

- [ ] Created `app/constants.py` with role enums and permission catalog
- [ ] Created role-to-permission mapping
- [ ] Created `require_permission()` dependency
- [ ] Created `require_org_member()` dependency (placeholder for Phase 5)
- [ ] Created `require_project_member()` dependency (placeholder for Phase 6)
- [ ] Added role escalation prevention logic
- [ ] Written unit tests for permission checking logic
- [ ] All existing tests still pass with authorization framework in place
