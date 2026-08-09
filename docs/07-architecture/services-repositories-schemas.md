# Service Layer, Repository Pattern, and Schemas

## Services

The service layer contains **business logic** — the rules and processes that define what your application does. Services:

- Orchestrate multiple repository calls within a transaction
- Enforce business rules (can a viewer assign tasks? is the project archived?)
- Trigger side effects (notifications, emails, audit logs)
- Do NOT know about HTTP (no Request/Response objects)

### Example: TaskService responsibilities
- Validate that the project exists and is not archived
- Check that the assignee is a project member
- Create the task record
- Create an audit log entry
- Send a notification to the assignee
- Enqueue a background email job

---

## Repositories

The repository layer abstracts **data access**. Each repository handles CRUD and complex queries for a single entity.

### Base Repository Pattern
A base repository provides generic CRUD methods:
- `create(data)` — Insert a new record
- `get_by_id(id)` — Fetch by primary key
- `get_all(filters, pagination)` — Fetch with filtering
- `update(id, data)` — Update fields
- `delete(id)` — Remove a record

Entity-specific repositories extend this with custom queries:
- `TaskRepository.get_by_project(project_id, filters)`
- `UserRepository.get_by_email(email)`
- `TaskRepository.get_overdue_tasks(org_id)`

---

## Schemas (DTOs)

Pydantic schemas define the shape of data at API boundaries.

### Schema Types

| Schema | Purpose | Example |
|---|---|---|
| `TaskBase` | Shared fields | title, description |
| `TaskCreate` | POST request body | title, description, assignee_id, priority |
| `TaskUpdate` | PATCH request body | all fields optional |
| `TaskResponse` | GET response | id, title, status, created_at (no internal fields) |
| `TaskDetail` | Detailed GET response | includes comments, attachments |
| `TaskListResponse` | Paginated list response | items, total, page, size |

### Key Rules
- Never return SQLAlchemy models directly from endpoints
- Response schemas control exactly what the client sees
- Create schemas enforce required fields
- Update schemas make all fields optional
- Internal fields (password_hash, internal_id) never appear in response schemas

---

## Clean Architecture Flow

```
Client Request
    ↓
Router (thin) → validates request, calls service
    ↓
Service (business logic) → enforces rules, calls repositories
    ↓
Repository (data access) → queries database
    ↓
Model (database) → defines schema
```

Each layer only depends on the layers below it. Testing is easy because you can mock any layer.

---

## What I Should Be Able to Do Afterward

- [ ] Implement the service-repository pattern
- [ ] Create a base repository with generic CRUD
- [ ] Design Pydantic schemas for different operations
- [ ] Keep endpoints thin by delegating to services
- [ ] Test each layer independently
