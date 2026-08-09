# Phase 17 — Docker

## Objective

Containerize the entire DevFlow application using Docker. Create production-quality Dockerfiles, a complete docker-compose.yml for development, and ensure the entire stack can be started with a single command.

---

## Concepts Learned

- Writing production Dockerfiles
- Multi-stage builds
- Docker Compose for multi-service orchestration
- Docker networking
- Volume management for persistent data
- Environment-specific configuration
- Health checks in Docker
- Image optimization

**Relevant docs**:
- `18-docker/docker.md`

---

## Features After This Phase

- [ ] `docker-compose up` starts the entire stack
- [ ] Application Dockerfile with multi-stage build
- [ ] Worker Dockerfile for background jobs
- [ ] All services (PostgreSQL, Redis, MinIO, MailHog) containerized
- [ ] Persistent volumes for data
- [ ] Health checks for all services
- [ ] Development and production Docker configurations

---

## Docker Services

| Service | Image | Purpose | Persistent Volume |
|---|---|---|---|
| `app` | Custom | FastAPI application | No |
| `worker` | Custom | Background job worker | No |
| `db` | postgres:15-alpine | PostgreSQL | Yes |
| `redis` | redis:7-alpine | Cache/queue | Yes |
| `minio` | minio/minio | Object storage | Yes |
| `mailhog` | mailhog/mailhog | Email testing | No |

---

## Completion Checklist

- [ ] Created `docker/Dockerfile` with multi-stage build
- [ ] Created `docker/Dockerfile.worker` for background workers
- [ ] Created `.dockerignore`
- [ ] Created `docker-compose.yml` with all services
- [ ] Created `docker-compose.prod.yml` for production overrides
- [ ] All services start with `docker-compose up`
- [ ] Migrations run automatically on app start (or via a separate command)
- [ ] Health checks configured for all services
- [ ] Volumes persist data across restarts
- [ ] Application runs as non-root user in container
- [ ] Image size is reasonable (<500MB)
- [ ] All tests pass in Docker environment
- [ ] `Makefile` with common commands (up, down, migrate, test, logs)
