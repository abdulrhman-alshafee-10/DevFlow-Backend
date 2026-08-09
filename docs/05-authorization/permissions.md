# Permissions System

## 1. What Is It?

A permissions system defines granular actions that users can perform, mapped to roles. Instead of checking "is this user an admin?", you check "does this user have the `tasks:delete` permission?" This decouples authorization logic from specific role names.

---

## 2. Why Does It Matter?

- **Flexibility** — Change what a role can do without modifying endpoint code
- **Clarity** — Each endpoint declares exactly what permission it requires
- **Testability** — Test permissions independently from roles
- **Future-proofing** — Add new roles without touching authorization logic

---

## 3–10. (Follows standard structure)

### DevFlow Permission Catalog

```
# Organization permissions
org:read, org:update, org:delete
org:members:read, org:members:invite, org:members:remove, org:members:update_role
org:billing:manage

# Project permissions
project:create, project:read, project:update, project:delete
project:members:manage

# Task permissions
task:create, task:read, task:update, task:delete
task:assign, task:update_status

# Comment permissions
comment:create, comment:read, comment:update, comment:delete

# Attachment permissions
attachment:upload, attachment:read, attachment:delete

# Notification permissions
notification:read, notification:update

# AI permissions
ai:analyze, ai:suggest

# Admin permissions
admin:audit_log:read
```

### How Permissions Are Checked

1. Request arrives at endpoint
2. `require_permission("task:create")` dependency is invoked
3. Dependency loads user's role for the current organization/project context
4. Role is mapped to permissions using the permission matrix
5. If the required permission is in the role's permission set → allow
6. If not → raise `InsufficientPermissionsError` (403)

### Ownership Override

Some operations allow the resource owner to act regardless of role:
- A MEMBER can edit their own tasks (even though only MANAGER+ can edit any task)
- A user can delete their own comments
- A user can update their own profile

This is **resource-level authorization**, which supplements RBAC.

---

## Prerequisites

- RBAC (see `05-authorization/rbac.md`)
- FastAPI dependency injection

---

## What I Should Be Able to Do Afterward

- [ ] Define a permission catalog for an application
- [ ] Map permissions to roles
- [ ] Implement permission checking as a reusable dependency
- [ ] Handle ownership-based permission overrides
- [ ] Add new permissions without changing endpoint code
