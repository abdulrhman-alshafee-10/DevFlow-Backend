# Authorization Overview

## 1. What Is It?

Authorization determines **what an authenticated user is allowed to do**. While authentication answers "Who are you?", authorization answers "Are you allowed to do this?" Authorization controls access to resources, endpoints, and operations based on user roles, permissions, and ownership.

---

## 2. Why Does It Matter?

Without authorization, any authenticated user can:
- Read other users' private data
- Modify other organizations' projects
- Delete tasks they don't own
- Promote themselves to admin
- Access billing or admin-only features

Authorization is the difference between "you can enter the building" and "you can enter this specific room."

---

## 3. When Should I Use It?

- **Every endpoint that modifies data** — Who can create, update, delete?
- **Every endpoint that reads private data** — Who can see this resource?
- **Admin operations** — Only certain roles can manage users, settings
- **Cross-tenant access** — Prevent organization A from seeing organization B's data

---

## 4. When Should I NOT Use It?

- **Public endpoints** — Health checks, public documentation
- **Authentication endpoints** — Login, register, password reset
- **When authentication hasn't been verified** — Authorization requires authentication first

---

## 5. How Does It Work?

### Authorization Strategies

| Strategy | How It Works | Use Case |
|---|---|---|
| **RBAC** (Role-Based) | Users have roles; roles have permissions | Organization/project membership |
| **ABAC** (Attribute-Based) | Policies based on attributes of user/resource/environment | Complex, dynamic rules |
| **Resource-Based** | Check ownership or membership for a specific resource | "Can this user edit this task?" |
| **Permission-Based** | Users/roles have explicit permissions | Granular control |

DevFlow uses a combination of **RBAC + Resource-Based + Permission-Based** authorization.

### Authorization Layers in DevFlow

```
Layer 1: Authentication
  → Is the user logged in? (JWT valid?)

Layer 2: Organization Access
  → Is the user a member of this organization?

Layer 3: Role Check
  → Does the user's role allow this operation?

Layer 4: Project Access
  → Is the user a member of this project?

Layer 5: Resource Ownership
  → Does the user own this specific resource? (for edit/delete)
```

---

## 6. How Does It Fit Into DevFlow?

Every API endpoint has authorization requirements:

```
GET  /organizations/{id}        → Must be a member of the org
POST /projects                   → Must be ADMIN+ in the org
PUT  /tasks/{id}                 → Must be assignee, creator, or MANAGER+ in project
DELETE /comments/{id}            → Must be comment author or ADMIN+ in org
POST /organizations/{id}/invite  → Must be ADMIN+ in the org
```

---

## 7. Common Mistakes

### Checking Only at the API Level

Authorization must be enforced at the data level too. If a user knows a task ID from another organization, the query itself must be scoped.

### Relying on Client-Side Checks

Never trust the frontend to enforce authorization. Always enforce on the server.

### Not Distinguishing Roles Across Contexts

A user might be OWNER in Organization A but VIEWER in Organization B. Roles are per-context, not global.

### Hardcoding Permission Checks

Instead of `if user.role == "admin"`, use a permission system: `if user.has_permission("tasks:delete")`.

---

## 8. Production Considerations

- **Audit logging** — Log all authorization decisions (especially denials)
- **Consistent error messages** — Return 403 without revealing why (don't say "you're not an admin")
- **Performance** — Cache permissions in Redis to avoid database lookups on every request
- **Testing** — Test every endpoint with every role to ensure proper access control

---

## 9. Prerequisites

- Authentication (see `04-authentication/`)
- Understanding of roles and permissions concepts

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain the difference between authentication and authorization
- [ ] Describe RBAC, ABAC, and resource-based authorization
- [ ] Design an authorization system for a multi-tenant application
- [ ] Implement authorization as FastAPI dependencies
- [ ] Audit authorization decisions
