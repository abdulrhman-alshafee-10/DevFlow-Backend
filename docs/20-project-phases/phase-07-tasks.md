# Phase 7 — Tasks and Comments

## Objective

Implement the core task management system — the heart of DevFlow. Tasks belong to projects, can be assigned to users, have statuses and priorities, and support threaded comments. This is the largest feature phase.

---

## Concepts Learned

- Complex CRUD with many relationships
- Status transitions and state machines
- Filtering, sorting, and searching
- Pagination with multiple strategies
- Nested resources (comments on tasks)
- Audit logging (who changed what and when)
- Ownership-based authorization (edit own tasks)

**Relevant docs**:
- `06-api-design/` (all files)
- `03-database/indexing.md`
- `03-database/transactions.md`

---

## Features After This Phase

- [ ] Create, read, update, delete tasks
- [ ] Assign tasks to project members
- [ ] Set task status (todo, in_progress, in_review, done, cancelled)
- [ ] Set task priority (low, medium, high, critical)
- [ ] Set task due date
- [ ] Filter tasks by status, priority, assignee, due date
- [ ] Sort tasks by various fields
- [ ] Search tasks by title/description
- [ ] Paginated task listing
- [ ] Add comments to tasks
- [ ] Edit and delete own comments
- [ ] Audit log for task changes

---

## Database Changes

### Task Model

```
Table: tasks
  id:              UUID (PK)
  project_id:      UUID (FK → projects, NOT NULL)
  title:           VARCHAR(500) (NOT NULL)
  description:     TEXT
  status:          VARCHAR(20) (default="todo")
  priority:        VARCHAR(20) (default="medium")
  creator_id:      UUID (FK → users, NOT NULL)
  assignee_id:     UUID (FK → users, nullable)
  due_date:        DATE (nullable)
  parent_task_id:  UUID (FK → tasks, nullable) — for subtasks
  position:        INTEGER (default=0) — ordering within a status column
  created_at:      TIMESTAMP WITH TIME ZONE
  updated_at:      TIMESTAMP WITH TIME ZONE

Indexes:
  - INDEX on project_id
  - INDEX on assignee_id
  - INDEX on creator_id
  - INDEX on (project_id, status) — composite for filtered listing
  - INDEX on due_date
  - GIN INDEX on tsvector(title || ' ' || description) — full-text search
```

### Comment Model

```
Table: comments
  id:         UUID (PK)
  task_id:    UUID (FK → tasks, NOT NULL)
  author_id:  UUID (FK → users, NOT NULL)
  content:    TEXT (NOT NULL)
  created_at: TIMESTAMP WITH TIME ZONE
  updated_at: TIMESTAMP WITH TIME ZONE

Indexes:
  - INDEX on task_id
  - INDEX on author_id
```

### AuditLog Model

```
Table: audit_log
  id:              UUID (PK)
  organization_id: UUID (FK → organizations, NOT NULL)
  entity_type:     VARCHAR(50) (NOT NULL) — "task", "project", "comment"
  entity_id:       UUID (NOT NULL)
  action:          VARCHAR(50) (NOT NULL) — "created", "updated", "deleted"
  actor_id:        UUID (FK → users, NOT NULL)
  changes:         JSONB — { "status": {"old": "todo", "new": "in_progress"} }
  created_at:      TIMESTAMP WITH TIME ZONE

Indexes:
  - INDEX on (entity_type, entity_id) — history for a specific entity
  - INDEX on organization_id
  - INDEX on actor_id
  - INDEX on created_at
```

---

## API Endpoints

### Tasks

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/projects/{project_id}/tasks` | Create task | Yes | task:create |
| GET | `/api/v1/projects/{project_id}/tasks` | List tasks (filtered, paginated) | Yes | task:read |
| GET | `/api/v1/tasks/{id}` | Get task details | Yes | task:read |
| PATCH | `/api/v1/tasks/{id}` | Update task | Yes | task:update (or own task) |
| DELETE | `/api/v1/tasks/{id}` | Delete task | Yes | task:delete |
| GET | `/api/v1/tasks/my` | Get tasks assigned to me | Yes | Authenticated |

### Task Filtering and Sorting

```
GET /api/v1/projects/{id}/tasks?status=in_progress&priority=high&assignee_id=uuid&search=login&sort_by=due_date&sort_order=asc&page=1&size=20
```

### Comments

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| POST | `/api/v1/tasks/{task_id}/comments` | Add comment | Yes | comment:create |
| GET | `/api/v1/tasks/{task_id}/comments` | List comments | Yes | comment:read |
| PATCH | `/api/v1/comments/{id}` | Edit comment | Yes | Author only |
| DELETE | `/api/v1/comments/{id}` | Delete comment | Yes | Author or ADMIN+ |

### Audit Log

| Method | Path | Description | Auth | Permission |
|---|---|---|---|---|
| GET | `/api/v1/tasks/{id}/history` | Get task change history | Yes | task:read |

---

## Testing Requirements

- Task CRUD operations with proper authorization
- Task filtering by status, priority, assignee, due date
- Task sorting by various fields
- Task search by title/description
- Pagination works correctly
- MEMBER can edit own tasks, not others'
- MANAGER+ can edit any task
- VIEWER can only read
- Comment CRUD with author-only edit/delete
- Audit log records all task changes
- Cannot create tasks in archived projects
- Assignee must be a project member

---

## Completion Checklist

- [ ] Created Task, Comment, and AuditLog models
- [ ] Generated and applied migrations
- [ ] Created task repository with filtering, sorting, pagination
- [ ] Created comment repository
- [ ] Created audit log repository
- [ ] Created task service with business logic
- [ ] Created comment service
- [ ] Implemented task filtering, sorting, and searching
- [ ] Implemented pagination for task listing
- [ ] Implemented audit logging for task changes
- [ ] Created all task and comment endpoints
- [ ] Ownership-based authorization (MEMBER can edit own tasks)
- [ ] Full-text search index on tasks
- [ ] All tests pass for every role
- [ ] Cross-organization task access denied
