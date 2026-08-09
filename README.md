# DevFlow — Complete FastAPI Learning Roadmap

> A production-grade SaaS project to learn FastAPI and backend engineering from fundamentals to deployment.

---

## 📋 How to Use This Documentation

1. **Read the overview section first** — understand the project, the stack, and the architecture
2. **Study each topic section** before implementing the corresponding phase
3. **Follow the project phases in order** — each phase builds on the previous ones
4. **Check off items** as you complete them
5. **Don't skip topics** — even "advanced" concepts have practical applications in this project

---

## 📚 Documentation Structure

### 00 — Overview
- [Project Overview](docs/00-overview/project-overview.md) — What we're building and why
- [Learning Objectives](docs/00-overview/learning-objectives.md) — Complete checklist of skills
- [Technology Stack](docs/00-overview/technology-stack.md) — Every tool and why it was chosen
- [Architecture Overview](docs/00-overview/architecture-overview.md) — System design and data flow

### 01 — Python Fundamentals
- [Async/Await](docs/01-python/async-await.md) — Asynchronous programming for web servers
- [Type Hints](docs/01-python/typing.md) — Type annotations for FastAPI and Pydantic
- [Exceptions](docs/01-python/exceptions.md) — Custom exception hierarchies
- [Decorators](docs/01-python/decorators.md) — Function decorators and closures
- [Dependency Management](docs/01-python/dependency-management.md) — pip, virtualenv, requirements

### 02 — FastAPI Core
- [Fundamentals](docs/02-fastapi/fundamentals.md) — Creating and running a FastAPI app
- [Routing](docs/02-fastapi/routing.md) — URL design and APIRouter
- [Request & Response](docs/02-fastapi/request-response.md) — Validation and serialization
- [Dependency Injection](docs/02-fastapi/dependency-injection.md) — Depends() and dependency chains
- [Middleware](docs/02-fastapi/middleware.md) — Request/response processing
- [Exception Handling](docs/02-fastapi/exception-handling.md) — Custom error responses
- [Lifespan](docs/02-fastapi/lifespan.md) — Startup and shutdown events

### 03 — Database
- [PostgreSQL](docs/03-database/postgresql.md) — Setup, types, and configuration
- [SQLAlchemy 2.x](docs/03-database/sqlalchemy.md) — Async ORM with type hints
- [Relationships](docs/03-database/relationships.md) — One-to-many, many-to-many, self-referential
- [Transactions](docs/03-database/transactions.md) — ACID, isolation levels, deadlocks
- [Indexing](docs/03-database/indexing.md) — B-tree, GIN, composite, partial indexes
- [Alembic](docs/03-database/alembic.md) — Database migrations

### 04 — Authentication
- [Overview](docs/04-authentication/authentication-overview.md) — Complete auth system design
- [Password Hashing](docs/04-authentication/password-hashing.md) — bcrypt and secure storage
- [JWT](docs/04-authentication/jwt.md) — Token creation, validation, and claims
- [Access & Refresh Tokens](docs/04-authentication/access-refresh-tokens.md) — Dual token strategy
- [OAuth2](docs/04-authentication/oauth2.md) — Authorization framework and grant types
- [OpenID Connect](docs/04-authentication/oidc.md) — Identity layer for social login
- [Email Verification](docs/04-authentication/email-verification.md) — Verify user email ownership
- [Password Reset](docs/04-authentication/password-reset.md) — Secure reset flow

### 05 — Authorization
- [Overview](docs/05-authorization/authorization-overview.md) — Authorization strategies
- [RBAC](docs/05-authorization/rbac.md) — Role-Based Access Control
- [Permissions](docs/05-authorization/permissions.md) — Granular permission system
- [Resource Authorization](docs/05-authorization/resource-authorization.md) — Ownership checks
- [Multi-Tenancy](docs/05-authorization/multi-tenancy.md) — Organization data isolation

### 06 — API Design
- [CRUD](docs/06-api-design/crud.md) — Create, Read, Update, Delete patterns
- [Pagination](docs/06-api-design/pagination.md) — Offset and cursor-based pagination
- [Filtering](docs/06-api-design/filtering.md) — Dynamic query filtering
- [Sorting](docs/06-api-design/sorting.md) — Sortable fields and ordering
- [Searching](docs/06-api-design/searching.md) — Text search strategies
- [Status Codes](docs/06-api-design/status-codes.md) — HTTP status code reference
- [API Versioning](docs/06-api-design/api-versioning.md) — Versioning strategies

### 07 — Architecture
- [Project Structure](docs/07-architecture/project-structure.md) — Directory layout and organization
- [Services, Repos, Schemas](docs/07-architecture/services-repositories-schemas.md) — Layered architecture

### 08 — Redis
- [Redis Basics](docs/08-redis/redis-basics.md) — Data structures, TTL, Pub/Sub
- [Caching](docs/08-redis/caching.md) — Cache-aside pattern and invalidation
- [Rate Limiting](docs/08-redis/rate-limiting.md) — Request throttling
- [Temporary Data](docs/08-redis/temporary-data.md) — Tokens, counters, sessions

### 09 — Background Jobs
- [Background Tasks](docs/09-background-jobs/background-tasks.md) — Queues, workers, retries, scheduling

### 10 — Real-Time
- [WebSockets](docs/10-realtime/websockets.md) — Bidirectional communication
- [WebSocket Authentication](docs/10-realtime/websocket-authentication.md) — Securing WS connections
- [Connection Management](docs/10-realtime/connection-management.md) — Rooms, broadcasting, scaling
- [Server-Sent Events](docs/10-realtime/server-sent-events.md) — One-way streaming

### 11 — Files
- [File Uploads](docs/11-files/file-uploads.md) — Upload, validate, store, download

### 12 — Email
- [Email System](docs/12-email/email-system.md) — Transactional email with templates

### 13 — Search
- [PostgreSQL Search](docs/13-search/postgres-search.md) — Full-text search with ranking

### 14 — AI
- [AI Architecture](docs/14-ai/ai-architecture.md) — LLM integration, streaming, RAG

### 15 — Security
- [Security Overview](docs/15-security/security-overview.md) — Complete security checklist
- [Web Vulnerabilities](docs/15-security/web-vulnerabilities.md) — CORS, CSRF, XSS, SQL injection

### 16 — Testing
- [Testing Overview](docs/16-testing/testing-overview.md) — Strategy, tools, and scenarios

### 17 — Observability
- [Observability](docs/17-observability/observability.md) — Logging, tracing, metrics, health checks

### 18 — Docker
- [Docker](docs/18-docker/docker.md) — Containerization and Docker Compose

### 19 — Deployment
- [Deployment](docs/19-deployment/deployment.md) — Nginx, HTTPS, CI/CD, production

---

## 🚀 Project Phases (Implementation Roadmap)

| Phase | Title | What You Build |
|---|---|---|
| [01](docs/20-project-phases/phase-01-foundation.md) | **Foundation** | FastAPI app, project structure, config, middleware |
| [02](docs/20-project-phases/phase-02-database.md) | **Database** | PostgreSQL, SQLAlchemy, Alembic, User CRUD |
| [03](docs/20-project-phases/phase-03-authentication.md) | **Authentication** | JWT, refresh tokens, email verification, password reset |
| [04](docs/20-project-phases/phase-04-authorization.md) | **Authorization** | RBAC, permissions, authorization dependencies |
| [05](docs/20-project-phases/phase-05-organizations.md) | **Organizations** | Multi-tenancy, invitations, membership |
| [06](docs/20-project-phases/phase-06-projects.md) | **Projects** | Project CRUD, project membership, archival |
| [07](docs/20-project-phases/phase-07-tasks.md) | **Tasks & Comments** | Task management, comments, audit log, search |
| [08](docs/20-project-phases/phase-08-notifications.md) | **Notifications** | Event-driven notifications, unread counts |
| [09](docs/20-project-phases/phase-09-realtime.md) | **Real-Time** | WebSockets, SSE, live updates |
| [10](docs/20-project-phases/phase-10-redis.md) | **Redis** | Caching, rate limiting, full Redis integration |
| [11](docs/20-project-phases/phase-11-background-jobs.md) | **Background Jobs** | Task queues, workers, retries, scheduling |
| [12](docs/20-project-phases/phase-12-files.md) | **Files** | File uploads, object storage, pre-signed URLs |
| [13](docs/20-project-phases/phase-13-search.md) | **Search** | Full-text search with PostgreSQL |
| [14](docs/20-project-phases/phase-14-ai.md) | **AI** | LLM integration, streaming, RAG |
| [15](docs/20-project-phases/phase-15-testing.md) | **Testing** | Comprehensive test suite |
| [16](docs/20-project-phases/phase-16-security.md) | **Security** | Security hardening and audit |
| [17](docs/20-project-phases/phase-17-docker.md) | **Docker** | Containerization and Compose |
| [18](docs/20-project-phases/phase-18-deployment.md) | **Deployment** | Nginx, HTTPS, CI/CD, production |

### ✅ [Final Checklist](docs/20-project-phases/final-checklist.md)

> Everything you should know after completing this project.

---

## 📊 Learning Progression

```
Weeks 1-2:   Foundation → Database → First CRUD
Weeks 3-4:   Authentication → Authorization
Weeks 5-6:   Organizations → Projects → Tasks
Weeks 7-8:   Notifications → Real-Time → Redis
Weeks 9-10:  Background Jobs → Files → Search
Weeks 11-12: AI → Testing → Security
Weeks 13-14: Docker → Deployment → Production

Total estimated time: 12-16 weeks (part-time)
```

---

## 🏗️ Core Database Entities

```
User ←→ Organization (via OrganizationMember)
User ←→ Project (via ProjectMember)
Organization → Project → Task → Comment
                              → Attachment
User → RefreshToken
User → Notification
Organization → Invitation
All → AuditLog
```

---

## 🔑 Key Principle

> **One project. Every concept. No shortcuts.**

This isn't a tutorial collection. It's a single, realistic project that teaches you every concept you need to build production-grade backends. Follow it from Phase 1 to Phase 18, and you'll emerge as a confident backend engineer.
