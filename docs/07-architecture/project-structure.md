# Project Structure

## 1. What Is It?

Project structure defines how your code files are organized into directories and modules. A good structure makes code easy to find, understand, and modify. A bad structure leads to circular imports, unclear ownership, and maintenance nightmares.

---

## 2. Why Does It Matter?

DevFlow will eventually have dozens of modules and hundreds of files. Without a clear structure:
- New developers can't find where things are
- Circular imports become common
- Changes in one area unexpectedly break others
- Testing becomes difficult

---

## DevFlow Project Structure

```
devflow/
├── alembic/                        # Database migrations
│   ├── versions/                   # Migration files
│   ├── env.py                      # Alembic configuration
│   └── script.py.mako              # Migration template
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application factory
│   ├── config.py                   # Settings (pydantic-settings)
│   ├── database.py                 # Engine, session factory
│   ├── dependencies.py             # Shared dependencies
│   ├── exceptions.py               # Exception hierarchy
│   ├── constants.py                # Enums, constants
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py             # Re-exports all models
│   │   ├── base.py                 # Base model with common fields
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── comment.py
│   │   ├── attachment.py
│   │   ├── notification.py
│   │   └── audit_log.py
│   │
│   ├── schemas/                    # Pydantic schemas (DTOs)
│   │   ├── __init__.py
│   │   ├── common.py               # Shared schemas (pagination, errors)
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── ...
│   │
│   ├── repositories/               # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                 # Base repository with CRUD
│   │   ├── user.py
│   │   ├── task.py
│   │   └── ...
│   │
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── task.py
│   │   ├── notification.py
│   │   ├── email.py
│   │   └── ai.py
│   │
│   ├── api/                        # HTTP layer
│   │   ├── __init__.py
│   │   ├── deps.py                 # API dependencies
│   │   └── v1/
│   │       ├── __init__.py         # Router aggregation
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── organizations.py
│   │       ├── projects.py
│   │       ├── tasks.py
│   │       ├── comments.py
│   │       ├── notifications.py
│   │       └── ai.py
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── correlation_id.py
│   │   └── rate_limit.py
│   │
│   ├── workers/                    # Background tasks
│   │   ├── __init__.py
│   │   ├── email_worker.py
│   │   └── notification_worker.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── security.py             # JWT, hashing utilities
│       ├── email.py                # Email sending
│       └── storage.py              # File storage utilities
│
├── tests/
│   ├── conftest.py                 # Shared fixtures
│   ├── factories.py                # Test data factories
│   ├── unit/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_repositories/
│   │   └── test_workers/
│   └── api/
│       ├── test_auth.py
│       ├── test_tasks.py
│       └── ...
│
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── nginx.conf
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
│
├── alembic.ini
├── pyproject.toml
├── docker-compose.yml
└── Makefile                        # Common commands
```

---

## Key Principles

1. **Import direction flows inward**: API → Services → Repositories → Models
2. **No circular imports**: Services don't import from API; Repositories don't import from Services
3. **One model per file**: Keeps files focused and manageable
4. **Schemas separate from models**: API shapes and database shapes are different
5. **Tests mirror source structure**: `app/services/task.py` → `tests/unit/test_services/test_task.py`

---

## What I Should Be Able to Do Afterward

- [ ] Organize a FastAPI project with clear separation of concerns
- [ ] Avoid circular imports through proper layering
- [ ] Know where to put new files (models, schemas, services, routes)
- [ ] Navigate a large codebase confidently
