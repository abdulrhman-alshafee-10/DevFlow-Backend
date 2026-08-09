# Architecture Overview

## System Architecture

DevFlow follows a **layered architecture** pattern that separates concerns into distinct layers, each with a clear responsibility.

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENTS                            │
│         (Web App, Mobile App, API Consumers)            │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   NGINX (Reverse Proxy)                 │
│            TLS Termination, Rate Limiting               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FASTAPI APPLICATION                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Middleware Layer                                 │   │
│  │  (CORS, Auth, Logging, Rate Limiting)            │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Router Layer (API Endpoints)                    │   │
│  │  /auth  /users  /orgs  /projects  /tasks  /ai    │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Dependency Injection Layer                      │   │
│  │  (Auth, DB Sessions, Permissions, Services)      │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Service Layer (Business Logic)                  │   │
│  │  AuthService, TaskService, NotificationService   │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Repository Layer (Data Access)                  │   │
│  │  UserRepo, TaskRepo, OrgRepo                     │   │
│  └──────────────────────┬───────────────────────────┘   │
│  ┌──────────────────────▼───────────────────────────┐   │
│  │  Model Layer (SQLAlchemy Models)                 │   │
│  │  User, Organization, Project, Task               │   │
│  └──────────────────────────────────────────────────┘   │
└─────────┬──────────────┬────────────────┬───────────────┘
          │              │                │
          ▼              ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  PostgreSQL  │ │    Redis     │ │  Object Storage  │
│  (Primary    │ │  (Cache,     │ │  (S3/MinIO)      │
│   Database)  │ │   Queues,    │ │                  │
│              │ │   Pub/Sub)   │ │                  │
└──────────────┘ └──────┬───────┘ └──────────────────┘
                        │
                        ▼
               ┌──────────────────┐
               │  Background      │
               │  Workers         │
               │  (Celery/ARQ)    │
               └──────────────────┘
```

---

## Application Layers Explained

### 1. Router Layer (Presentation)

**Responsibility**: Accept HTTP requests, validate input, return HTTP responses.

- Defines API endpoints with HTTP methods
- Uses Pydantic schemas for request/response validation
- Delegates all business logic to the service layer
- Should contain minimal logic — just routing and response formatting

### 2. Dependency Injection Layer

**Responsibility**: Provide shared resources and cross-cutting concerns to routes.

- Database session management
- Current user extraction from JWT
- Permission checking
- Service instantiation
- Configuration access

### 3. Service Layer (Business Logic)

**Responsibility**: Implement business rules and orchestrate operations.

- Contains all business logic
- Coordinates between repositories
- Handles transactions
- Triggers side effects (notifications, emails, background jobs)
- Does NOT know about HTTP (no request/response objects)

### 4. Repository Layer (Data Access)

**Responsibility**: Abstract database operations.

- CRUD operations on database models
- Complex queries with filters, joins, and aggregations
- Returns domain objects (SQLAlchemy models)
- Does NOT contain business logic
- Makes it easy to swap data sources (e.g., for testing)

### 5. Model Layer (Domain)

**Responsibility**: Define the database schema and relationships.

- SQLAlchemy model definitions
- Table relationships (foreign keys, back_populates)
- Database constraints (unique, check, not null)
- Indexes for query performance

### 6. Schema Layer (DTOs)

**Responsibility**: Define data shapes for input validation and output serialization.

- Request schemas (what the client sends)
- Response schemas (what the API returns)
- Internal schemas (for service-to-service communication)
- Computed fields and validators

---

## Data Flow Example: Creating a Task

```
Client sends POST /api/v1/projects/{id}/tasks
    │
    ▼
Router: Validates request body with TaskCreate schema
    │
    ▼
Dependencies: Extracts current user from JWT, gets DB session
    │
    ▼
Dependencies: Checks user has permission to create tasks in project
    │
    ▼
Service: TaskService.create_task()
    ├── Validates business rules (project exists, assignee is member, etc.)
    ├── Calls TaskRepository.create() to insert into database
    ├── Calls NotificationService.notify() to alert assignee
    └── Enqueues background job to send email notification
    │
    ▼
Router: Returns TaskResponse with 201 status code
```

---

## Multi-Tenancy Model

DevFlow uses **organization-based multi-tenancy** where data isolation is enforced at the application level:

```
Organization A                    Organization B
├── Project A1                    ├── Project B1
│   ├── Task A1-1                 │   ├── Task B1-1
│   └── Task A1-2                 │   └── Task B1-2
└── Project A2                    └── Project B2
    └── Task A2-1                     └── Task B2-1
```

- All data belongs to an organization
- Users access data through organization membership
- Every query is scoped to the user's organization
- Cross-organization data access is prevented at the repository level

---

## Communication Patterns

### Synchronous (Request/Response)

- **REST API** — Standard CRUD operations
- Used for: creating tasks, updating profiles, fetching data

### Asynchronous (Background)

- **Task Queue** — Operations that don't need immediate response
- Used for: sending emails, processing uploads, AI analysis

### Real-Time (Push)

- **WebSockets** — Bidirectional communication
- Used for: chat, live task updates, presence

- **Server-Sent Events** — Server-to-client streaming
- Used for: notifications, AI response streaming

---

## Directory Structure (Target)

```
devflow/
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # Settings management
│   ├── database.py             # Database connection setup
│   ├── dependencies.py         # Shared dependencies
│   ├── exceptions.py           # Custom exceptions
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── project.py
│   │   ├── task.py
│   │   └── ...
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── task.py
│   │   └── ...
│   │
│   ├── repositories/           # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── user.py
│   │   └── ...
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── task.py
│   │   └── ...
│   │
│   ├── api/                    # Route definitions
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── organizations.py
│   │   │   ├── projects.py
│   │   │   ├── tasks.py
│   │   │   └── ...
│   │   └── deps.py             # API-specific dependencies
│   │
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── rate_limit.py
│   │
│   ├── workers/                # Background task definitions
│   │   ├── __init__.py
│   │   ├── email.py
│   │   └── notifications.py
│   │
│   └── utils/                  # Utility functions
│       ├── __init__.py
│       ├── security.py
│       └── email.py
│
├── tests/                      # Test suite
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── docker/                     # Docker configuration
├── docs/                       # This documentation
├── alembic.ini
├── pyproject.toml
├── requirements.txt
└── docker-compose.yml
```

---

## Key Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastAPI | Async-first, type-safe, automatic docs |
| Database | PostgreSQL | Relational integrity, full-text search, JSON support |
| ORM | SQLAlchemy 2.x | Async support, powerful queries, migration tool |
| Auth | JWT (access + refresh) | Stateless, scalable, standard approach |
| Multi-tenancy | Application-level | Simpler than schema/database-per-tenant, sufficient for most SaaS |
| File storage | Object storage (S3) | Scalable, cheap, CDN-friendly |
| Background jobs | Task queue (Celery/ARQ) | Reliable, retryable, scalable |
| Real-time | WebSockets + SSE | WS for bidirectional, SSE for unidirectional streaming |
| Search | PostgreSQL FTS → Elasticsearch | Start simple, upgrade when needed |
| Architecture | Layered (Router → Service → Repository) | Clear separation, testable, maintainable |
