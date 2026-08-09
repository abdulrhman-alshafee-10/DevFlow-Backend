# Technology Stack

## Core Framework

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.11+ | Primary language — async support, type hints, rich ecosystem |
| **FastAPI** | 0.100+ | Web framework — async-first, automatic validation, OpenAPI docs |
| **Uvicorn** | Latest | ASGI server — production-grade async server for FastAPI |

### Why FastAPI?

- **Performance** — One of the fastest Python frameworks, comparable to Node.js and Go
- **Type safety** — Built on Pydantic, catches errors before they reach production
- **Automatic docs** — OpenAPI/Swagger documentation generated from your code
- **Async native** — First-class support for async/await
- **Modern Python** — Leverages type hints, dataclasses, and modern Python patterns
- **Developer experience** — Excellent error messages, auto-complete support

---

## Data Layer

| Technology | Purpose |
|---|---|
| **PostgreSQL** | Primary relational database — robust, feature-rich, excellent for complex queries |
| **SQLAlchemy 2.x** | ORM — modern async support, powerful query builder, migration support |
| **Alembic** | Database migrations — version control for your database schema |
| **asyncpg** | Async PostgreSQL driver — high-performance async database access |

### Why PostgreSQL?

- Full-text search built in (we'll use this before introducing Elasticsearch)
- JSONB columns for semi-structured data
- Excellent indexing options (B-tree, GIN, GiST)
- Row-level security for multi-tenancy
- Mature, battle-tested, widely used in production

### Why SQLAlchemy 2.x?

- The 2.x release introduced native async support
- Declarative model definitions with type hints
- Powerful relationship loading strategies (lazy, eager, selectin)
- Works seamlessly with Alembic for migrations
- Large community and excellent documentation

---

## Validation & Serialization

| Technology | Purpose |
|---|---|
| **Pydantic v2** | Data validation and serialization — fast, type-safe, integrates with FastAPI |

### Why Pydantic?

- FastAPI is built on top of Pydantic — they're inseparable
- Validates incoming data automatically
- Serializes outgoing data with control over what's exposed
- Generates JSON Schema for documentation
- v2 is significantly faster than v1 (written in Rust)

---

## Caching & In-Memory Store

| Technology | Purpose |
|---|---|
| **Redis** | Caching, rate limiting, session storage, pub/sub, temporary data |

### Why Redis?

- Sub-millisecond response times
- Built-in TTL (time-to-live) for automatic expiration
- Pub/sub for real-time features
- Atomic operations for rate limiting
- Widely used, well-documented, easy to set up

---

## Background Processing

| Technology | Purpose |
|---|---|
| **Celery** or **ARQ** | Task queues — async background job processing |
| **Redis** (as broker) | Message broker for task queues |

### Celery vs. ARQ

| Feature | Celery | ARQ |
|---|---|---|
| Maturity | Very mature, widely used | Newer, lighter |
| Async | Partial async support | Fully async (built on asyncio) |
| Complexity | More complex setup | Simpler setup |
| Features | Rich (beat, chains, groups) | Core features |
| Community | Large | Smaller |

**Recommendation**: Start with ARQ for simplicity if you want a fully async stack. Use Celery if you need advanced features like periodic tasks (Celery Beat), task chains, or canvas workflows.

---

## Real-Time

| Technology | Purpose |
|---|---|
| **WebSockets** (built into FastAPI) | Bidirectional real-time communication — chat, live updates |
| **Server-Sent Events** | One-way server-to-client streaming — notifications, AI response streaming |

---

## File Storage

| Technology | Purpose |
|---|---|
| **MinIO** (dev) / **AWS S3** (prod) | Object storage — file uploads, attachments |

### Why MinIO?

- S3-compatible API — same code works with AWS S3 in production
- Runs locally in Docker — no cloud account needed for development
- Free and open source

---

## Email

| Technology | Purpose |
|---|---|
| **FastAPI-Mail** or **aiosmtplib** | Async email sending |
| **Jinja2** | HTML email templates |
| **MailHog** (dev) | Local email testing — captures emails without sending them |

---

## Search

| Technology | Purpose |
|---|---|
| **PostgreSQL FTS** | Built-in full-text search — good enough for many use cases |
| **Elasticsearch** (optional) | Advanced search — faceting, fuzzy matching, relevance tuning |

---

## AI / LLM

| Technology | Purpose |
|---|---|
| **OpenAI API** / **Anthropic API** | LLM integration — task analysis, summarization, suggestions |
| **LangChain** (optional) | LLM orchestration — chains, agents, RAG pipelines |
| **pgvector** (optional) | Vector storage in PostgreSQL — for RAG embeddings |

---

## Testing

| Technology | Purpose |
|---|---|
| **pytest** | Test framework — fixtures, parametrize, plugins |
| **pytest-asyncio** | Async test support |
| **httpx** | Async HTTP client for testing FastAPI |
| **factory-boy** | Test data factories |
| **Faker** | Realistic fake data generation |

---

## Security

| Technology | Purpose |
|---|---|
| **passlib[bcrypt]** | Password hashing |
| **python-jose** or **PyJWT** | JWT creation and validation |
| **python-multipart** | Form data and file upload parsing |

---

## DevOps & Deployment

| Technology | Purpose |
|---|---|
| **Docker** | Containerization |
| **Docker Compose** | Multi-container orchestration for development |
| **Nginx** | Reverse proxy, TLS termination, static files |
| **GitHub Actions** | CI/CD pipeline |
| **Gunicorn** | Process manager for Uvicorn workers in production |

---

## Observability

| Technology | Purpose |
|---|---|
| **structlog** | Structured logging — JSON logs, correlation IDs |
| **Prometheus** (optional) | Metrics collection |
| **Grafana** (optional) | Metrics visualization |

---

## Development Tools

| Tool | Purpose |
|---|---|
| **Ruff** | Linting and formatting (replaces flake8, black, isort) |
| **mypy** | Static type checking |
| **pre-commit** | Git hooks for code quality |
| **httpie** or **curl** | Manual API testing |

---

## Version Summary

```
Python          >= 3.11
FastAPI         >= 0.100
SQLAlchemy      >= 2.0
Pydantic        >= 2.0
PostgreSQL      >= 15
Redis           >= 7.0
Docker          >= 24.0
Docker Compose  >= 2.20
```

> **Note**: Exact versions may change. Always check the official documentation for the latest compatible versions when you start building.
