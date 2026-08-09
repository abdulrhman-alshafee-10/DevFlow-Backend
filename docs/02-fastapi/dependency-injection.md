# Dependency Injection in FastAPI

## 1. What Is It?

Dependency injection (DI) is a design pattern where a function's dependencies are provided to it rather than created by it. In FastAPI, DI is implemented through the `Depends()` function, which lets you declare that an endpoint needs certain resources (database sessions, current user, permissions) and FastAPI will provide them automatically.

---

## 2. Why Does It Matter?

FastAPI's DI system is one of its most powerful features:

- **Reusability** — Write common logic once, inject it everywhere
- **Testability** — Swap dependencies in tests (e.g., use a test database)
- **Separation of concerns** — Endpoints don't need to know how to create database sessions
- **Composability** — Dependencies can depend on other dependencies, forming a chain
- **Security** — Authentication and authorization are implemented as dependencies

---

## 3. When Should I Use It?

- **Database sessions** — Every endpoint that queries the database
- **Current user extraction** — Parsing JWT and loading the user
- **Permission checks** — Verifying the user has access to a resource
- **Service instantiation** — Creating service objects with their dependencies
- **Configuration** — Providing settings to endpoints
- **Pagination** — Extracting and validating pagination parameters
- **Rate limiting** — Checking request counts

---

## 4. When Should I NOT Use It?

- **Simple computations** — If it's just a utility function, call it directly
- **One-off logic** — If it's only used in one place and isn't about shared resources
- **When it creates deep chains** — More than 3-4 levels of dependency nesting becomes hard to follow

---

## 5. How Does It Work?

### Basic Dependency

A dependency is just a function (or callable) that FastAPI calls before your endpoint:

```
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

@app.get("/users")
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]):
    ...
```

### Dependency Chains

Dependencies can depend on other dependencies:

```
get_db → get_current_user → check_admin_permission
```

FastAPI resolves the entire chain automatically.

### Yield Dependencies

Dependencies that use `yield` provide cleanup:

```
async def get_db():
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
```

### Class Dependencies

Dependencies can be classes, which is useful for parameterized dependencies:

```
class Pagination:
    def __init__(self, page: int = 1, size: int = 20):
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
```

---

## 6. How Does It Fit Into DevFlow?

DevFlow's dependency chain:

```
get_db()                          → Database session
get_current_user(db, token)       → Authenticated user
get_current_active_user(user)     → User is not deactivated
require_org_member(user, org_id)  → User belongs to organization
require_project_access(user, project_id) → User has project access
require_permission(permission)    → User has specific permission
get_task_service(db)             → Service with injected repository
```

This means an endpoint like "update task" automatically:
1. Gets a database session
2. Extracts and validates the JWT
3. Loads the current user
4. Verifies the user is active
5. Checks organization membership
6. Verifies project access
7. Checks the specific permission (e.g., `tasks:update`)
8. Creates the task service with the database session

All before your endpoint code runs.

---

## 7. Common Mistakes

### Creating Database Sessions Manually

Let the DI system manage database sessions. Manual session creation leads to leaked connections.

### Not Using `Annotated` (Modern Style)

The modern pattern uses `Annotated` for cleaner, reusable dependencies.

### Circular Dependencies

If A depends on B and B depends on A, FastAPI will error. Restructure to break the cycle.

### Heavy Computation in Dependencies

Dependencies run on every request. Don't put expensive operations in them.

### Not Testing Dependencies Independently

Dependencies should be testable on their own, not just through endpoints.

---

## 8. Production Considerations

- **Performance** — Dependencies are called on every request; keep them lightweight
- **Caching** — FastAPI caches dependency results within a single request by default
- **Error handling** — Exceptions in dependencies propagate correctly to exception handlers
- **Cleanup** — Use `yield` dependencies for resources that need cleanup (connections, locks)
- **Overrides** — Use `app.dependency_overrides` for testing

---

## 9. Prerequisites

- FastAPI fundamentals (see `02-fastapi/fundamentals.md`)
- Python generators and `yield`
- Type hints and `Annotated`

---

## 10. What I Should Be Able to Do Afterward

- [ ] Create function and class dependencies
- [ ] Use `Depends()` and `Annotated` syntax
- [ ] Build dependency chains for authentication and authorization
- [ ] Use `yield` dependencies for resource cleanup
- [ ] Override dependencies for testing
- [ ] Design a dependency hierarchy for a multi-tenant application
