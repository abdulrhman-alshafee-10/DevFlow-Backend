# Phase 6 — Projects

## Objective

Implement projects within organizations. Projects are containers for tasks and have their own membership and role system. This phase introduces project-level authorization layered on top of organization-level access.

---

## Concepts Learned

- Nested resources (projects within organizations)
- Project-level membership and roles
- Layered authorization (org access → project access)
- Archiving vs. deleting
- Cascading relationships

**Relevant docs**:
- `05-authorization/resource-authorization.md`
- `03-database/relationships.md`

---

## Features After This Phase

- [ ] Create projects within an organization
- [ ] Project creator becomes MANAGER
- [ ] Add/remove project members (from org members)
- [ ] Assign project-level roles (MANAGER, MEMBER, VIEWER)
- [ ] Archive projects (soft-disable without deleting)
- [ ] List projects within an organization (with pagination/filtering)

---

## Database Changes

### Project Model

```
Table: projects
  id:              UUID (PK)
  organization_id: UUID (FK → organizations, NOT NULL)
  name:            VARCHAR(255) (NOT NULL)
  slug:            VARCHAR(255) (NOT NULL)
  description:     TEXT
  status:          VARCHAR(20) (default="active") — active, archived
  created_by:      UUID (FK → users, NOT NULL)
  created_at:      TIMESTAMP WITH TIME ZONE
  updated_at:      TIMESTAMP WITH TIME ZONE

  UNIQUE(organization_id, slug)

Indexes:
  - UNIQUE on (organization_id, slug)
  - INDEX on organization_id
  - INDEX on created_by
```

### ProjectMember Model

```
Table: project_members
  id:          UUID (PK)
  project_id:  UUID (FK → projects, NOT NULL)
  user_id:     UUID (FK → users, NOT NULL)
  role:        VARCHAR(20) (NOT NULL) — MANAGER, MEMBER, VIEWER
  added_at:    TIMESTAMP WITH TIME ZONE

  UNIQUE(project_id, user_id)

Indexes:
  - UNIQUE on (project_id, user_id)
  - INDEX on user_id
```

---

## API Endpoints

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/organizations/{org_id}/projects` | Create project | Yes | project:create |
| GET | `/api/v1/organizations/{org_id}/projects` | List org projects | Yes | org:read |
| GET | `/api/v1/projects/{id}` | Get project details | Yes | project:read |
| PATCH | `/api/v1/projects/{id}` | Update project | Yes | project:update |
| DELETE | `/api/v1/projects/{id}` | Delete project | Yes | project:delete |
| POST | `/api/v1/projects/{id}/archive` | Archive project | Yes | project:update |
| POST | `/api/v1/projects/{id}/unarchive` | Unarchive project | Yes | project:update |
| GET | `/api/v1/projects/{id}/members` | List project members | Yes | project:read |
| POST | `/api/v1/projects/{id}/members` | Add project member | Yes | project:members:manage |
| PATCH | `/api/v1/projects/{id}/members/{user_id}` | Update member role | Yes | project:members:manage |
| DELETE | `/api/v1/projects/{id}/members/{user_id}` | Remove project member | Yes | project:members:manage |

---

## Testing Requirements

- Create project → creator becomes MANAGER, project belongs to correct org
- Non-org-member cannot create project → 403
- Archived project blocks task creation (tested in Phase 7)
- Cross-org project access denied
- Project member operations respect project-level roles
- Org ADMIN can manage any project in their org
- Project VIEWER cannot modify project

---

## Completion Checklist

- [ ] Created Project and ProjectMember models
- [ ] Generated and applied migrations
- [ ] Created project repository and service
- [ ] Created project CRUD endpoints
- [ ] Created project member management endpoints
- [ ] Implemented `require_project_member()` dependency
- [ ] Implemented archive/unarchive functionality
- [ ] Project queries scoped by organization
- [ ] All role/permission tests pass
- [ ] Cross-organization access tests pass
