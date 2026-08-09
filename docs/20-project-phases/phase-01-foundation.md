# Phase 1 — Foundation

## Objective

Set up the project from scratch: create the FastAPI application, configure the development environment, establish the project structure, and implement basic health endpoints. This is the "hello world" phase — but done properly.

---

## Concepts Learned

- Creating a FastAPI application
- Project structure and module organization
- Configuration management with pydantic-settings
- Environment variables and `.env` files
- Virtual environments and dependency management
- Running the app with Uvicorn
- Basic routing and path operations
- Custom exception handling
- Middleware (CORS, request logging)
- Application lifespan events
- API versioning with URL prefixes

**Relevant docs**:
- `01-python/` (all files)
- `02-fastapi/` (all files)
- `07-architecture/project-structure.md`

---

## Features After This Phase

- [ ] FastAPI application runs with `uvicorn`
- [ ] Project structure follows the layered architecture
- [ ] Configuration loaded from environment variables
- [ ] Health check endpoint returns application status
- [ ] CORS middleware configured
- [ ] Request logging middleware with correlation IDs
- [ ] Custom exception handlers return consistent error format
- [ ] API documentation available at `/docs` (Swagger UI)
- [ ] API is versioned under `/api/v1/`

---

## Database Changes

**None** — Database is set up in Phase 2.

---

## API Endpoints

| Method | Path | Description | Auth Required |
|---|---|---|---|
| GET | `/health` | Basic health check | No |
| GET | `/health/ready` | Readiness check (placeholder — no DB yet) | No |
| GET | `/api/v1/` | API root / welcome message | No |

---

## Authentication/Authorization Requirements

None in this phase. Everything is public.

---

## Testing Requirements

- Health check returns 200 with `{"status": "healthy"}`
- Readiness check returns 200
- Unknown routes return 404 with consistent error format
- CORS headers are present in responses
- Request logging middleware logs request method, path, and duration

---

## Completion Checklist

- [ ] Created virtual environment and installed dependencies
- [ ] Created `requirements/base.txt` and `requirements/dev.txt`
- [ ] Set up project directory structure (`app/`, `tests/`, `docs/`)
- [ ] Created `app/main.py` with FastAPI application factory
- [ ] Created `app/config.py` with pydantic-settings for configuration
- [ ] Created `.env` file with development settings
- [ ] Added `.gitignore` for Python projects
- [ ] Implemented health check endpoints
- [ ] Added CORS middleware
- [ ] Added request logging middleware with correlation IDs
- [ ] Created custom exception hierarchy (`app/exceptions.py`)
- [ ] Registered exception handlers for custom exceptions
- [ ] Created API v1 router structure (`app/api/v1/`)
- [ ] Application runs with `uvicorn app.main:app --reload`
- [ ] Swagger UI is accessible at `/docs`
- [ ] Written first tests (health check, error format)
- [ ] Initialized Git repository with first commit
