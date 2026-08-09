# Phase 2 — Database Setup

## Objective

Connect FastAPI to PostgreSQL using SQLAlchemy 2.x with async support. Create the User model, set up Alembic for migrations, and implement basic user CRUD operations. This phase establishes the data layer that everything else builds on.

---

## Concepts Learned

- PostgreSQL setup and configuration
- SQLAlchemy 2.x with async support (asyncpg)
- Declarative model definitions with type hints
- Database session management as FastAPI dependencies
- Alembic initialization and first migration
- Base model with common fields (id, created_at, updated_at)
- UUID primary keys
- Repository pattern for data access
- Service layer for business logic
- Pydantic schemas for request/response validation
- CRUD operations

**Relevant docs**:
- `03-database/` (all files)
- `06-api-design/crud.md`
- `07-architecture/services-repositories-schemas.md`

---

## Features After This Phase

- [ ] PostgreSQL database connected with async SQLAlchemy
- [ ] User model with proper fields and constraints
- [ ] Alembic configured for database migrations
- [ ] First migration creates the users table
- [ ] Base repository with generic CRUD operations
- [ ] User repository with email lookup
- [ ] User service with business logic
- [ ] User CRUD endpoints (temporary — will be restricted after auth)
- [ ] Database session dependency with proper lifecycle

---

## Database Changes

### User Model

```
Table: users
  id:                UUID (PK, default=uuid4)
  email:             VARCHAR(255) (UNIQUE, NOT NULL)
  username:          VARCHAR(100) (UNIQUE, NOT NULL)
  hashed_password:   VARCHAR(255) (NOT NULL)
  full_name:         VARCHAR(255)
  is_active:         BOOLEAN (default=true)
  is_email_verified: BOOLEAN (default=false)
  is_superuser:      BOOLEAN (default=false)
  avatar_url:        VARCHAR(500)
  created_at:        TIMESTAMP WITH TIME ZONE (default=now)
  updated_at:        TIMESTAMP WITH TIME ZONE (default=now, onupdate=now)

Indexes:
  - UNIQUE on email
  - UNIQUE on username
```

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/users` | Create a user (temporary, for testing) | No |
| GET | `/api/v1/users` | List users (paginated) | No |
| GET | `/api/v1/users/{id}` | Get user by ID | No |
| PATCH | `/api/v1/users/{id}` | Update user | No |
| DELETE | `/api/v1/users/{id}` | Delete user | No |

> **Note**: These endpoints are temporary and unprotected. In Phase 3, they'll be locked behind authentication. In Phase 4, they'll be restricted by authorization.

---

## Authentication/Authorization Requirements

None yet — endpoints are open for testing. This is intentional: you need to verify the data layer works before adding auth.

---

## Testing Requirements

- **Database connection**: App starts and connects to the test database
- **Create user**: POST returns 201 with user data (no password hash in response)
- **Duplicate email**: POST returns 409 when email already exists
- **Get user**: GET returns 200 with user data
- **Get non-existent user**: GET returns 404
- **Update user**: PATCH returns 200 with updated fields
- **Delete user**: DELETE returns 204
- **List users**: GET returns paginated list
- **Pagination**: Page and size parameters work correctly
- **Schema validation**: Missing required fields return 422

---

## Completion Checklist

- [ ] PostgreSQL running (Docker or local installation)
- [ ] Created `app/database.py` with async engine and session factory
- [ ] Created `app/models/base.py` with base model class (id, timestamps)
- [ ] Created `app/models/user.py` with User model
- [ ] Initialized Alembic: `alembic init -t async alembic`
- [ ] Configured `alembic/env.py` for async and auto-discovery of models
- [ ] Generated first migration: `alembic revision --autogenerate -m "create users table"`
- [ ] Reviewed and applied migration: `alembic upgrade head`
- [ ] Created database session dependency with `yield`
- [ ] Created `app/repositories/base.py` with generic CRUD
- [ ] Created `app/repositories/user.py` with user-specific queries
- [ ] Created `app/schemas/user.py` (UserCreate, UserUpdate, UserResponse)
- [ ] Created `app/schemas/common.py` (PaginatedResponse, ErrorResponse)
- [ ] Created `app/services/user.py` with business logic
- [ ] Created `app/api/v1/users.py` with CRUD endpoints
- [ ] Verified Swagger UI shows all endpoints with correct schemas
- [ ] Written unit tests for user service
- [ ] Written API tests for user CRUD endpoints
- [ ] Verified response schemas don't expose `hashed_password`
