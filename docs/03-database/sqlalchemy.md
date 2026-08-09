# SQLAlchemy 2.x

## 1. What Is It?

SQLAlchemy is Python's most popular Object-Relational Mapper (ORM). It lets you define database tables as Python classes and interact with the database using Python objects instead of raw SQL. Version 2.x is a major rewrite with native async support, improved type hints, and a more modern API.

---

## 2. Why Does It Matter?

Writing raw SQL for every database operation is error-prone and repetitive. SQLAlchemy provides:

- **Object mapping** — Work with Python objects instead of raw rows
- **Type safety** — Type-checked queries with IDE support
- **Relationship handling** — Automatically load related objects (user → organization → projects)
- **Query building** — Compose complex queries with Python code
- **Database abstraction** — Switch databases without rewriting queries
- **Migration support** — Alembic generates migrations from model changes
- **Async support** — Native `async/await` with `asyncpg`

---

## 3. When Should I Use It?

- **Application development** — Any time you interact with a relational database
- **Complex domains** — When you have many related entities
- **When you need relationships** — Automatic join loading, cascading deletes
- **When you want migration support** — Track schema changes over time

---

## 4. When Should I NOT Use It?

- **Simple scripts** — For a one-off query, raw SQL with `asyncpg` is simpler
- **Bulk operations** — Loading millions of rows through the ORM is slow; use `COPY` or raw SQL
- **Complex analytics queries** — Some analytical queries are easier in raw SQL
- **When raw SQL performance matters** — The ORM adds overhead (usually negligible)

---

## 5. How Does It Work?

### Declarative Models

Define tables as Python classes using `DeclarativeBase`:

```
class User:
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID]               # Column definition
    email: Mapped[str]                   # Required string column
    created_at: Mapped[datetime]         # Timestamp column
    tasks: Mapped[list["Task"]]          # Relationship (one-to-many)
```

### Session Management

The `AsyncSession` is your interface to the database:
- `session.add(obj)` — Stage an insert
- `session.execute(query)` — Run a query
- `session.commit()` — Persist staged changes
- `session.rollback()` — Undo staged changes
- `session.refresh(obj)` — Reload from database

### Query Building

SQLAlchemy 2.x uses `select()` for queries:

```
select(User).where(User.email == "...")
select(Task).join(Project).where(Project.org_id == org_id)
select(func.count()).select_from(Task).where(Task.status == "done")
```

### Relationship Loading Strategies

| Strategy | When | How |
|---|---|---|
| `lazy="select"` | Access the attribute later | Separate query per access |
| `lazy="selectin"` | Load with parent | One extra query per relationship |
| `lazy="joined"` | Always need together | JOIN in the same query |
| `lazy="raise"` | Never auto-load | Raises error if accessed (prevents N+1) |

---

## 6. How Does It Fit Into DevFlow?

DevFlow's core models:

```
User ──────┐
           ├── OrganizationMember ──── Organization
           ├── ProjectMember ───────── Project
           ├── Task (as assignee/creator)
           ├── Comment
           ├── Notification
           └── RefreshToken

Organization ──── Project ──── Task ──── Comment
                                   └──── Attachment

Organization ──── Invitation

User/Organization/Project/Task ──── AuditLog
```

All models use:
- **UUID primary keys** — Globally unique, not guessable
- **Timestamps** — `created_at`, `updated_at` on all models
- **Soft deletes** (optional) — `deleted_at` instead of actual deletion
- **Async sessions** — All database operations are async

---

## 7. Common Mistakes

### N+1 Query Problem

Loading a list of tasks then accessing `task.assignee` for each one generates N+1 queries. Use `selectinload()` or `joinedload()` to load relationships eagerly.

### Not Using `async` Session Properly

Forgetting to `await` session operations or using sync sessions with async code.

### Not Committing Transactions

`session.add()` stages the change but doesn't persist it. You must call `await session.commit()`.

### Mixing Model and Schema Concerns

SQLAlchemy models are for the database; Pydantic schemas are for the API. Don't return SQLAlchemy models directly from endpoints.

### Not Handling Session Lifecycle

Sessions should be created per request and closed afterward. Use FastAPI dependencies with `yield`.

---

## 8. Production Considerations

- **Connection pool sizing** — Match the pool size to your expected concurrency. Too small → connection waiting; too large → database overload
- **Query logging** — Log slow queries (>100ms) for optimization
- **Relationship loading** — Default to `lazy="raise"` to catch N+1 issues in development
- **Bulk operations** — Use `session.execute(insert(Model).values([...]))` for batch inserts
- **Read replicas** — Route read queries to replicas for scaling

---

## 9. Prerequisites

- Basic SQL
- Python classes and inheritance
- Type hints (see `01-python/typing.md`)
- Async/await (see `01-python/async-await.md`)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define SQLAlchemy models with typed columns
- [ ] Create async database sessions with FastAPI dependencies
- [ ] Perform CRUD operations using the async session
- [ ] Write queries with `select()`, `where()`, `join()`
- [ ] Use relationship loading strategies correctly
- [ ] Avoid N+1 query problems
- [ ] Understand session lifecycle and transaction management
