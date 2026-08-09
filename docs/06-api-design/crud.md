# CRUD Operations

## 1. What Is It?

CRUD stands for **Create, Read, Update, Delete** — the four fundamental operations for persistent data. In a REST API, CRUD maps to HTTP methods:

| Operation | HTTP Method | Example | Status Code |
|---|---|---|---|
| **Create** | POST | `POST /tasks` | 201 Created |
| **Read (list)** | GET | `GET /tasks` | 200 OK |
| **Read (single)** | GET | `GET /tasks/{id}` | 200 OK |
| **Update (full)** | PUT | `PUT /tasks/{id}` | 200 OK |
| **Update (partial)** | PATCH | `PATCH /tasks/{id}` | 200 OK |
| **Delete** | DELETE | `DELETE /tasks/{id}` | 204 No Content |

---

## 2. Why Does It Matter?

Every feature in DevFlow is built on CRUD. Understanding the patterns means you can implement any resource endpoint quickly and consistently.

---

## 3–6. How Does It Fit Into DevFlow?

### Standard CRUD for Each Resource

Every major entity (tasks, projects, comments, etc.) follows the same pattern:

1. **Create** — Validate input, check permissions, insert, return created resource
2. **Read** — Check permissions, fetch with relationships, return
3. **List** — Check permissions, query with filters/pagination/sorting, return paginated list
4. **Update** — Check permissions, validate partial input, update only provided fields
5. **Delete** — Check permissions, soft-delete or hard-delete, return 204

### PUT vs. PATCH

- **PUT** replaces the entire resource (all fields required)
- **PATCH** updates only the provided fields (optional fields)

**DevFlow uses PATCH** for updates because users rarely want to replace an entire task — they usually change one field (status, assignee, due date).

---

## What I Should Be Able to Do Afterward

- [ ] Implement CRUD endpoints for any resource
- [ ] Use appropriate HTTP methods and status codes
- [ ] Handle partial updates with PATCH
- [ ] Apply consistent patterns across all resources
- [ ] Connect CRUD operations through the service/repository layers
