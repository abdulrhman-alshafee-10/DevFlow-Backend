# FastAPI Routing

## 1. What Is It?

Routing is the mechanism that maps incoming HTTP requests to the correct handler function based on the URL path and HTTP method. In FastAPI, routes are defined using decorators on functions (called "path operations").

---

## 2. Why Does It Matter?

A well-organized routing system is the public interface of your API. It determines:

- What URLs your API exposes
- What HTTP methods each URL accepts
- How your API is structured and discovered
- How your codebase is organized as it grows

---

## 3. When Should I Use It?

Routing is used for every endpoint in your API. The key decisions are:

- **How to organize routes** — By resource, feature, or domain
- **When to use `APIRouter`** — For grouping related routes in separate files
- **When to use path prefixes** — For nesting resources
- **When to use tags** — For organizing documentation

---

## 4. When Should I NOT Use It?

- **Don't create routes for internal operations** — Not everything needs an endpoint
- **Don't create deeply nested routes** — `/orgs/{id}/projects/{id}/tasks/{id}/comments/{id}/attachments/{id}` is too deep; flatten it
- **Don't create routes that duplicate functionality** — One way to do each thing

---

## 5. How Does It Work?

### Path Operations

FastAPI provides decorators for each HTTP method:

- `@app.get("/path")` — Read data
- `@app.post("/path")` — Create data
- `@app.put("/path")` — Replace data
- `@app.patch("/path")` — Partially update data
- `@app.delete("/path")` — Delete data

### Path Parameters

Dynamic segments in the URL:

```
/users/{user_id}          → user_id is a path parameter
/projects/{project_id}    → project_id is a path parameter
```

FastAPI validates the type automatically based on your type hint.

### Query Parameters

Parameters after `?` in the URL:

```
/tasks?status=active&page=1&size=20
```

Any parameter in your function that isn't a path parameter becomes a query parameter.

### APIRouter

For organizing routes into separate files:

```
Router defined in:     api/v1/tasks.py
Mounted in main app:   app.include_router(task_router, prefix="/api/v1")
```

### Route Organization Patterns

```
api/
└── v1/
    ├── auth.py           # /api/v1/auth/*
    ├── users.py          # /api/v1/users/*
    ├── organizations.py  # /api/v1/organizations/*
    ├── projects.py       # /api/v1/projects/*
    ├── tasks.py          # /api/v1/tasks/*
    ├── comments.py       # /api/v1/comments/*
    └── ...
```

---

## 6. How Does It Fit Into DevFlow?

DevFlow's route structure:

```
/api/v1/auth/                    # Authentication
/api/v1/users/                   # User management
/api/v1/organizations/           # Organization CRUD
/api/v1/organizations/{id}/members/  # Organization membership
/api/v1/projects/                # Project CRUD
/api/v1/projects/{id}/members/   # Project membership
/api/v1/tasks/                   # Task CRUD
/api/v1/tasks/{id}/comments/     # Task comments
/api/v1/tasks/{id}/attachments/  # Task attachments
/api/v1/notifications/           # Notifications
/api/v1/invitations/             # Team invitations
/api/v1/search/                  # Search
/api/v1/ai/                      # AI features
/ws/                             # WebSocket connections
```

Each group is defined in a separate file with an `APIRouter`, then mounted in the main application with the appropriate prefix.

---

## 7. Common Mistakes

### Not Using APIRouter

Putting all routes in `main.py` creates a monolithic file that's impossible to navigate.

### Inconsistent URL Patterns

Mix of `/getUsers`, `/users/list`, `/user-all`. Pick a convention (plural nouns, lowercase, hyphens) and stick with it.

### Using Query Parameters for Required Data

If a piece of data is required to identify a resource, it should be a path parameter, not a query parameter.

### Route Order Matters

FastAPI matches routes in order. `/users/me` must be defined before `/users/{user_id}`, or `me` will be treated as a user_id.

### Not Using Tags

Tags organize your Swagger documentation. Without them, all endpoints appear in one long list.

---

## 8. Production Considerations

- **API versioning** — Use a version prefix (`/api/v1/`) from the start
- **Rate limiting** — Apply at the route or router level
- **Documentation** — Use `summary`, `description`, and `tags` for clear API docs
- **Deprecation** — Mark old endpoints as deprecated instead of removing them immediately
- **URL length** — Keep URLs reasonable; deeply nested resources can be flattened

---

## 9. Prerequisites

- FastAPI fundamentals (see `02-fastapi/fundamentals.md`)
- HTTP methods and URL structure
- Type hints (see `01-python/typing.md`)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define routes with path and query parameters
- [ ] Use `APIRouter` to organize routes into modules
- [ ] Mount routers with prefixes and tags
- [ ] Design a consistent URL structure for a REST API
- [ ] Handle route ordering correctly
- [ ] Use response_model and status_code on routes
