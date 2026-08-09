# Resource-Level Authorization

## 1. What Is It?

Resource-level authorization checks whether a user can access or modify a **specific resource** (a particular task, comment, or attachment). While RBAC answers "can this role perform this action?", resource-level authorization answers "can this user perform this action on **this specific resource**?"

---

## 2. Why Does It Matter?

RBAC alone isn't enough. A MEMBER in Organization A can create tasks — but they shouldn't be able to edit tasks in Organization B. Resource-level authorization ensures:

- Users only access resources within their organization
- Users only modify resources they own or have permission for
- Cross-tenant data leakage is impossible

---

## 3–6. How Does It Fit Into DevFlow?

### Authorization Chain

```
1. Is the user authenticated? (JWT valid)
2. Is the user a member of this organization? (org membership check)
3. Does the user's role have the required permission? (RBAC)
4. Does the user have access to this specific resource? (resource-level)
   a. Is the resource in the user's organization?
   b. Is the user a member of the resource's project?
   c. Is the user the owner of this resource? (for edit/delete)
```

### Patterns

- **Scoped queries** — Always filter by organization_id in queries
- **Ownership checks** — Compare resource.creator_id with current_user.id
- **Membership verification** — Check project/org membership before accessing nested resources

---

## What I Should Be Able to Do Afterward

- [ ] Implement resource ownership checks
- [ ] Scope all database queries to the user's organization
- [ ] Verify membership before accessing nested resources
- [ ] Prevent IDOR (Insecure Direct Object Reference) vulnerabilities
- [ ] Combine RBAC with resource-level checks in a single dependency chain
