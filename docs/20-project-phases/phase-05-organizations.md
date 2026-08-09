# Phase 5 — Organizations

## Objective

Implement multi-tenant organizations. Users can create organizations, invite members, and manage roles. All subsequent features (projects, tasks) will exist within an organization context, ensuring data isolation.

---

## Concepts Learned

- Multi-tenancy with organization-scoped data
- Many-to-many relationships via association tables
- Invitation system (create, send, accept, reject, expire)
- Organization-level role management
- Data isolation (queries scoped by organization)
- Cascading operations

**Relevant docs**:
- `05-authorization/multi-tenancy.md`
- `03-database/relationships.md`
- `12-email/email-system.md`

---

## Features After This Phase

- [ ] Create and manage organizations
- [ ] Organization creator becomes OWNER
- [ ] Invite users to organizations via email
- [ ] Accept or reject invitations
- [ ] Manage member roles (promote/demote)
- [ ] Remove members from organizations
- [ ] List organizations the current user belongs to
- [ ] Switch between organizations
- [ ] Data isolation between organizations

---

## Database Changes

### Organization Model

```
Table: organizations
  id:           UUID (PK)
  name:         VARCHAR(255) (NOT NULL)
  slug:         VARCHAR(255) (UNIQUE, NOT NULL)
  description:  TEXT
  avatar_url:   VARCHAR(500)
  is_active:    BOOLEAN (default=true)
  created_by:   UUID (FK → users)
  created_at:   TIMESTAMP WITH TIME ZONE
  updated_at:   TIMESTAMP WITH TIME ZONE
```

### OrganizationMember Model

```
Table: organization_members
  id:              UUID (PK)
  organization_id: UUID (FK → organizations, NOT NULL)
  user_id:         UUID (FK → users, NOT NULL)
  role:            VARCHAR(20) (NOT NULL) — OWNER, ADMIN, MEMBER, VIEWER
  joined_at:       TIMESTAMP WITH TIME ZONE
  
  UNIQUE(organization_id, user_id)

Indexes:
  - UNIQUE on (organization_id, user_id)
  - INDEX on user_id
```

### Invitation Model

```
Table: invitations
  id:              UUID (PK)
  organization_id: UUID (FK → organizations, NOT NULL)
  email:           VARCHAR(255) (NOT NULL)
  role:            VARCHAR(20) (NOT NULL, default="MEMBER")
  invited_by:      UUID (FK → users, NOT NULL)
  token:           VARCHAR(255) (UNIQUE, NOT NULL)
  status:          VARCHAR(20) (NOT NULL) — pending, accepted, rejected, expired
  expires_at:      TIMESTAMP WITH TIME ZONE (NOT NULL)
  created_at:      TIMESTAMP WITH TIME ZONE

Indexes:
  - UNIQUE on token
  - INDEX on (organization_id, email)
  - INDEX on email
```

---

## API Endpoints

### Organizations

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/organizations` | Create organization | Yes | Authenticated user |
| GET | `/api/v1/organizations` | List my organizations | Yes | Authenticated user |
| GET | `/api/v1/organizations/{id}` | Get organization details | Yes | org:read |
| PATCH | `/api/v1/organizations/{id}` | Update organization | Yes | org:update |
| DELETE | `/api/v1/organizations/{id}` | Delete organization | Yes | OWNER only |

### Organization Members

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| GET | `/api/v1/organizations/{id}/members` | List members | Yes | org:members:read |
| PATCH | `/api/v1/organizations/{id}/members/{user_id}` | Update member role | Yes | org:members:update_role |
| DELETE | `/api/v1/organizations/{id}/members/{user_id}` | Remove member | Yes | org:members:remove |

### Invitations

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/organizations/{id}/invitations` | Send invitation | Yes | org:members:invite |
| GET | `/api/v1/organizations/{id}/invitations` | List pending invitations | Yes | org:members:invite |
| DELETE | `/api/v1/invitations/{id}` | Cancel invitation | Yes | org:members:invite |
| POST | `/api/v1/invitations/{token}/accept` | Accept invitation | Yes | Invited user |
| POST | `/api/v1/invitations/{token}/reject` | Reject invitation | Yes | Invited user |
| GET | `/api/v1/invitations/pending` | My pending invitations | Yes | Authenticated |

---

## Authentication/Authorization Requirements

- Create organization: any authenticated user
- Organization operations: must be a member of the organization
- Role-specific operations: checked against permission mapping
- OWNER cannot be removed (organization must always have an owner)
- Users cannot change their own role
- Users cannot assign a role higher than their own

---

## Testing Requirements

- Create organization → creator becomes OWNER
- List organizations → only shows user's organizations
- Cross-organization access → 403
- Invite user → sends email with invitation link
- Accept invitation → user becomes member with specified role
- Reject invitation → invitation status changes
- Expired invitation → 400
- Duplicate invitation → 409
- Remove member → user loses access
- Cannot remove OWNER
- Role update → permissions change accordingly
- Role escalation prevention (ADMIN can't make someone OWNER)

---

## Completion Checklist

- [ ] Created Organization and OrganizationMember models
- [ ] Created Invitation model
- [ ] Generated and applied migrations
- [ ] Created organization repository and service
- [ ] Created invitation repository and service
- [ ] Created organization CRUD endpoints
- [ ] Created member management endpoints
- [ ] Created invitation endpoints
- [ ] Implemented `require_org_member()` dependency
- [ ] All queries scoped by organization_id
- [ ] Invitation emails sent via background task
- [ ] Cross-organization access tested and denied
- [ ] Role-based permission tests for all endpoints
- [ ] OWNER protection tests (cannot be removed/demoted)
