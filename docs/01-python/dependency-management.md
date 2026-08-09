# Python Dependency Management

## 1. What Is It?

Dependency management is the practice of tracking, installing, and updating the external libraries (packages) your project needs. In Python, this involves tools like `pip`, virtual environments, `requirements.txt`, and `pyproject.toml`.

---

## 2. Why Does It Matter?

A production backend like DevFlow depends on dozens of packages (FastAPI, SQLAlchemy, Pydantic, etc.). Without proper dependency management:

- **Reproducibility breaks** — Works on your machine but fails in production
- **Version conflicts** — Package A needs library v1, Package B needs library v2
- **Security risks** — Outdated dependencies may have known vulnerabilities
- **Collaboration suffers** — Teammates can't set up the project

---

## 3. When Should I Use It?

- **Every Python project** — Even small scripts benefit from virtual environments
- **When adding new libraries** — Always pin versions
- **Before deployment** — Lock exact versions for reproducibility
- **Regularly** — Audit and update dependencies for security patches

---

## 4. When Should I NOT Use It?

- There is no case where you should skip dependency management in a serious project

---

## 5. How Does It Work?

### Virtual Environments

A virtual environment is an isolated Python installation for your project:

```
python -m venv venv          # Create
source venv/bin/activate     # Activate (Linux/Mac)
venv\Scripts\activate        # Activate (Windows)
```

### Requirements Files

The traditional approach — list dependencies in `requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
```

Split into multiple files for different needs:

```
requirements/
├── base.txt        # Core dependencies
├── dev.txt         # Development tools (pytest, ruff, mypy)
└── prod.txt        # Production-only (gunicorn, sentry-sdk)
```

### pyproject.toml (Modern Approach)

The modern standard for Python project configuration. Consolidates metadata, dependencies, and tool configuration in one file.

### Pinning vs. Ranges

```
fastapi==0.104.1        # Pinned: exactly this version
fastapi>=0.100,<1.0     # Range: compatible versions
fastapi~=0.104.1        # Compatible release: >=0.104.1, <0.105.0
```

**Production**: Pin exact versions for reproducibility.
**Libraries**: Use ranges for flexibility.

---

## 6. How Does It Fit Into DevFlow?

DevFlow's dependency structure:

**Core dependencies** (`requirements/base.txt`):
- `fastapi` — Web framework
- `uvicorn[standard]` — ASGI server
- `sqlalchemy[asyncio]` — ORM with async support
- `asyncpg` — Async PostgreSQL driver
- `alembic` — Database migrations
- `pydantic[email]` — Validation with email support
- `python-jose[cryptography]` — JWT handling
- `passlib[bcrypt]` — Password hashing
- `redis[hiredis]` — Redis client with C extension
- `httpx` — Async HTTP client
- `python-multipart` — File upload support
- `jinja2` — Email templates

**Development dependencies** (`requirements/dev.txt`):
- `pytest`, `pytest-asyncio` — Testing
- `httpx` — Test client
- `factory-boy`, `faker` — Test data
- `ruff` — Linting and formatting
- `mypy` — Type checking
- `pre-commit` — Git hooks

**Production dependencies** (`requirements/prod.txt`):
- `gunicorn` — Process manager
- `sentry-sdk` — Error tracking

---

## 7. Common Mistakes

### Not Using a Virtual Environment

Installing packages globally leads to version conflicts between projects.

### Not Pinning Versions

`pip install fastapi` installs the latest version. Tomorrow, a new version might break your code.

### Forgetting Transitive Dependencies

Your code depends on `fastapi`, which depends on `starlette`, which depends on `anyio`. A change in any of these can break your app. Use `pip freeze > requirements.lock` to capture exact versions.

### Not Separating Dev and Prod Dependencies

Installing `pytest` and `ruff` in production wastes resources and increases attack surface.

### Ignoring Security Advisories

Use `pip-audit` or `safety` to check for known vulnerabilities in your dependencies.

---

## 8. Production Considerations

- **Lock files** — Use `pip freeze` or `pip-compile` (from pip-tools) to lock exact versions
- **Minimal installs** — Only install production dependencies in the Docker image
- **Multi-stage Docker builds** — Install build dependencies in one stage, copy only runtime files to the final image
- **Vulnerability scanning** — Integrate `pip-audit` into your CI/CD pipeline
- **Private packages** — Use a private PyPI server or Git URLs for internal packages
- **Reproducibility** — Given the same lock file, every install should produce the same environment

---

## 9. Prerequisites

- Basic Python installation
- Command-line familiarity
- Understanding of what packages/libraries are

---

## 10. What I Should Be Able to Do Afterward

- [ ] Create and use a Python virtual environment
- [ ] Manage dependencies with pip and requirements files
- [ ] Pin dependency versions for reproducibility
- [ ] Separate dev and production dependencies
- [ ] Use `pip freeze` to capture exact versions
- [ ] Audit dependencies for security vulnerabilities
- [ ] Understand `pyproject.toml` configuration
