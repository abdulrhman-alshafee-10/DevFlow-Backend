# Role-Based Access Control (RBAC)

## 1. What Is It?

RBAC assigns users to roles, and roles define what actions are permitted. Instead of giving permissions directly to users, you assign roles (like ADMIN or MEMBER), and each role comes with a predefined set of permissions.

---

## 2. Why Does It Matter?

RBAC simplifies permission management:
- Instead of managing permissions for 1000 users individually, manage 5 roles
- New team members get a role and immediately have the right permissions
- Changing a role's permissions affects all users with that role

---

## 3. When Should I Use It?

- **Team-based applications** — Where users have different levels of access
- **Organization hierarchy** — Owners, admins, members, viewers
- **When permissions map cleanly to roles** — Most SaaS applications

---

## 4. When Should I NOT Use It?

- **Fine-grained per-resource permissions** — RBAC alone doesn't handle "user X can edit task Y but not task Z"
- **Dynamic policies** — "Allow access only during business hours" needs ABAC
- **Flat applications** — If everyone has the same access, roles add unnecessary complexity

---

## 5. How Does It Work?

### DevFlow Role Hierarchy

```
OWNER   → Full control (billing, delete org, manage all members)
  ↓
ADMIN   → Manage members, projects, settings
  ↓
MANAGER → Manage tasks, assign work, manage project members
  ↓
MEMBER  → Create/edit own tasks, comment, upload files
  ↓
VIEWER  → Read-only access to projects and tasks
```

### Role Contexts

Roles exist in specific contexts:

| Context | Roles | Assigned Via |
|---|---|---|
| **Organization** | OWNER, ADMIN, MEMBER, VIEWER | OrganizationMember table |
| **Project** | MANAGER, MEMBER, VIEWER | ProjectMember table |

A user can have different roles in different organizations and projects.

### Permission Matrix

| Permission | OWNER | ADMIN | MANAGER | MEMBER | VIEWER |
|---|---|---|---|---|---|
| Delete organization | ✓ | | | | |
| Manage billing | ✓ | | | | |
| Invite members | ✓ | ✓ | | | |
| Remove members | ✓ | ✓ | | | |
| Create projects | ✓ | ✓ | | | |
| Delete projects | ✓ | ✓ | | | |
| Manage project members | ✓ | ✓ | ✓ | | |
| Create tasks | ✓ | ✓ | ✓ | ✓ | |
| Assign tasks | ✓ | ✓ | ✓ | | |
| Edit any task | ✓ | ✓ | ✓ | | |
| Edit own tasks | ✓ | ✓ | ✓ | ✓ | |
| Delete tasks | ✓ | ✓ | ✓ | | |
| Comment | ✓ | ✓ | ✓ | ✓ | |
| View projects/tasks | ✓ | ✓ | ✓ | ✓ | ✓ |
| Upload files | ✓ | ✓ | ✓ | ✓ | |

---

## 6. How Does It Fit Into DevFlow?

### Implementation Approach

1. Define roles as Python enums
2. Map permissions to roles in a configuration (not hardcoded in endpoints)
3. Create a `require_permission()` dependency that checks the user's role against the required permission
4. Apply the dependency to each endpoint

### Role Assignment

- Organization creator → OWNER
- Invited user → MEMBER (default) or specified role
- Project creator → MANAGER (within that project)
- Project member → MEMBER (default) or specified role

---

## 7. Common Mistakes

### Hardcoding Role Checks

Don't check `if role == "admin"` in every endpoint. Use a permission system that maps roles to permissions.

### Not Supporting Multiple Roles

A user can be ADMIN in one organization and VIEWER in another. The role depends on context.

### Role Hierarchy Without Inheritance

If ADMIN has all MANAGER permissions plus more, implement role inheritance rather than duplicating permissions.

### Not Seeding the OWNER Role

The organization creator must automatically become OWNER. If this fails, no one can manage the organization.

---

## 8. Production Considerations

- **Role changes** — When a user's role changes, their cached permissions must be invalidated
- **Audit trail** — Log role assignments and changes
- **Least privilege** — Default to the most restrictive role
- **Role escalation prevention** — Users cannot assign roles higher than their own

---

## 9. Prerequisites

- Authorization overview (see `05-authorization/authorization-overview.md`)
- Database relationships (for membership tables)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Design a role hierarchy for a multi-tenant application
- [ ] Map permissions to roles
- [ ] Implement role checking as FastAPI dependencies
- [ ] Handle roles across different contexts (organization, project)
- [ ] Prevent role escalation attacks
