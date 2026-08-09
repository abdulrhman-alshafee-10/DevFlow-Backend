# Multi-Tenancy

## 1. What Is It?

Multi-tenancy is an architecture where a single application instance serves multiple tenants (organizations/companies), keeping their data strictly isolated. Each tenant sees only their own data, as if they have their own private instance.

---

## 2. Why Does It Matter?

DevFlow is a SaaS platform. Multiple organizations use the same application. Without proper multi-tenancy:
- Organization A could see Organization B's projects and tasks
- A bug in one tenant's data could affect another
- Compliance requirements (GDPR, SOC 2) would be violated

---

## 3–5. How Does It Work?

### Multi-Tenancy Strategies

| Strategy | Isolation | Complexity | DevFlow Choice |
|---|---|---|---|
| **Separate databases** | Highest | Highest (manage N databases) | No |
| **Separate schemas** | High | Medium (migrations × N schemas) | No |
| **Shared schema, row-level** | Medium | Lowest | **Yes** |

### DevFlow's Approach: Shared Schema with Row-Level Isolation

All tenants share the same tables. Every table that contains tenant-specific data has an `organization_id` column. Every query includes a WHERE clause filtering by the current user's organization.

### Enforcement Layers

1. **Repository layer** — Every query method accepts `org_id` and includes it in the WHERE clause
2. **Service layer** — Extracts `org_id` from the current user's context
3. **Database constraints** — Foreign keys ensure referential integrity within an organization
4. **Testing** — Tests verify that cross-tenant access is impossible

---

## 6. How Does It Fit Into DevFlow?

### Tenant-Scoped Tables

```
organizations                (the tenant itself)
projects                     → organization_id
tasks                        → project_id → organization_id
comments                     → task_id → project_id → organization_id
attachments                  → task_id → ...
notifications                → user_id + organization_id
audit_log                    → organization_id
invitations                  → organization_id
organization_members         → organization_id
project_members              → project_id → organization_id
```

### Key Rule

**Every query must be scoped to the user's organization.** There are no exceptions. Even admin queries within your own system should be scoped.

---

## What I Should Be Able to Do Afterward

- [ ] Explain the three multi-tenancy strategies and their tradeoffs
- [ ] Implement row-level tenant isolation
- [ ] Ensure every query is scoped to the current tenant
- [ ] Test that cross-tenant data access is impossible
- [ ] Handle users who belong to multiple organizations
