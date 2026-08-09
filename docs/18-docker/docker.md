# Docker and Docker Compose

## 1. What Is It?

Docker packages your application and all its dependencies into a container — a lightweight, portable, self-contained unit that runs the same way everywhere. Docker Compose orchestrates multiple containers (app, database, Redis) as a single environment.

---

## 2. Why Does It Matter?

- **"Works on my machine"** — Docker eliminates environment differences between development, testing, and production
- **Reproducibility** — Same container = same behavior everywhere
- **Isolation** — Each service runs in its own container with its own dependencies
- **Easy setup** — New developers run `docker-compose up` and everything works
- **Production parity** — Development environment matches production

---

## DevFlow Docker Architecture

```
docker-compose.yml orchestrates:

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   FastAPI     │  │  PostgreSQL  │  │    Redis     │
│   App         │  │   Database   │  │              │
│   :8000       │  │   :5432      │  │   :6379      │
└──────┬───────┘  └──────────────┘  └──────────────┘
       │
┌──────┴───────┐  ┌──────────────┐  ┌──────────────┐
│   Worker     │  │   MinIO      │  │   MailHog    │
│  (Celery/    │  │   (S3)       │  │   (Email)    │
│   ARQ)       │  │   :9000      │  │   :8025      │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Dockerfile Best Practices

### Multi-Stage Build

```
Stage 1 (builder): Install dependencies, compile extensions
Stage 2 (runtime): Copy only what's needed, run as non-root user
```

### Key Practices
- **Use slim base images** — `python:3.11-slim` not `python:3.11`
- **Order layers by frequency of change** — Requirements before code (caching)
- **Don't run as root** — Create a non-root user
- **Use `.dockerignore`** — Exclude `.git`, `__pycache__`, `tests/`, `docs/`
- **Pin base image versions** — `python:3.11.7-slim` not `python:3.11`
- **Health checks** — Add `HEALTHCHECK` instruction

---

## Docker Compose Services

| Service | Image | Purpose | Ports |
|---|---|---|---|
| `app` | Custom (Dockerfile) | FastAPI application | 8000 |
| `worker` | Custom (Dockerfile.worker) | Background job worker | — |
| `db` | `postgres:15-alpine` | PostgreSQL database | 5432 |
| `redis` | `redis:7-alpine` | Cache, queue broker | 6379 |
| `minio` | `minio/minio` | Object storage | 9000, 9001 |
| `mailhog` | `mailhog/mailhog` | Email testing | 1025, 8025 |

### Networking

All services communicate on a shared Docker network using service names:
- App connects to `db:5432`, not `localhost:5432`
- App connects to `redis:6379`, not `localhost:6379`

### Volumes

Persist data across container restarts:
- `postgres_data:/var/lib/postgresql/data`
- `minio_data:/data`
- `redis_data:/data`

---

## Production Dockerfile Considerations

- **No development dependencies** — Don't include pytest, ruff in production
- **Multi-stage builds** — Minimize final image size
- **Security scanning** — Scan images with Trivy or Docker Scout
- **Non-root user** — Run the app as a non-root user
- **Read-only filesystem** — Mount the container filesystem as read-only where possible
- **Resource limits** — Set CPU and memory limits in deployment

---

## What I Should Be Able to Do Afterward

- [ ] Write a production-quality Dockerfile for a FastAPI app
- [ ] Use multi-stage builds for smaller images
- [ ] Create a docker-compose.yml with all DevFlow services
- [ ] Manage Docker volumes for data persistence
- [ ] Configure Docker networking between services
- [ ] Understand Docker layer caching for faster builds
