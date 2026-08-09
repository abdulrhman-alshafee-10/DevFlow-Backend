# Production Deployment

## 1. What Is It?

Production deployment is the process of making your application available to real users. It encompasses infrastructure setup, configuration management, CI/CD pipelines, HTTPS, reverse proxying, and monitoring.

---

## Production Architecture

```
Internet
    │
    ▼
┌─────────────────────┐
│    Load Balancer     │  (Cloud provider LB or Nginx)
│    + TLS/HTTPS       │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌─────────┐
│ App     │ │ App     │    Gunicorn + Uvicorn workers
│ Server 1│ │ Server 2│    (horizontal scaling)
└────┬────┘ └────┬────┘
     │           │
     ├───────────┤
     ▼           ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│   DB    │ │  Redis  │ │   S3     │
│ Primary │ │ Primary │ │  Bucket  │
│   +     │ │   +     │ │          │
│ Replica │ │ Replica │ │          │
└─────────┘ └─────────┘ └──────────┘
```

---

## Nginx Configuration

Nginx serves as a reverse proxy in front of FastAPI:
- **TLS termination** — Handles HTTPS certificates
- **Static file serving** — Serves static assets efficiently
- **Request buffering** — Protects backend from slow clients
- **Rate limiting** — First line of defense
- **Compression** — Gzip responses for smaller payloads
- **Load balancing** — Distributes requests across app instances

---

## HTTPS / TLS

- **Always use HTTPS in production** — No exceptions
- Use **Let's Encrypt** for free TLS certificates with auto-renewal
- Configure **HSTS** (HTTP Strict Transport Security) to force HTTPS
- Set TLS minimum version to 1.2

---

## CI/CD Pipeline

### GitHub Actions Workflow

```
On push to main:
  1. Lint (ruff check)
  2. Type check (mypy)
  3. Run tests (pytest)
  4. Build Docker image
  5. Push to container registry
  6. Deploy to staging
  7. Run smoke tests
  8. Deploy to production (manual approval)
  9. Run health checks
```

### Deployment Strategies

| Strategy | How | Risk | Rollback |
|---|---|---|---|
| **Rolling** | Replace instances one at a time | Low | Reverse the rolling update |
| **Blue-Green** | Deploy new version alongside old; switch traffic | Very low | Switch back to old version |
| **Canary** | Send small % of traffic to new version | Lowest | Route all traffic back to old |

---

## Environment Management

### Environment Variables (not hardcoded!)

```
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/devflow
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generated-secret>
JWT_SECRET_KEY=<generated-secret>
ALLOWED_ORIGINS=https://app.devflow.com
EMAIL_HOST=smtp.sendgrid.net
AI_API_KEY=sk-...
ENVIRONMENT=production
DEBUG=false
```

### Secrets Management
- **Never** commit secrets to Git
- Use environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets periodically
- Different secrets for each environment (dev, staging, prod)

---

## Database Migrations in Production

```
1. Backup the database
2. Run migrations: alembic upgrade head
3. Deploy new code
4. Verify application health
5. If issues: rollback code, run: alembic downgrade -1
```

### Zero-Downtime Migrations

For changes that can't be applied atomically:
1. **Deploy code that handles both old and new schema**
2. **Run migration** (add new column as nullable)
3. **Backfill data** (populate new column)
4. **Deploy code that uses new column**
5. **Add NOT NULL constraint** (if needed)
6. **Remove old code paths**

---

## What I Should Be Able to Do Afterward

- [ ] Configure Nginx as a reverse proxy for FastAPI
- [ ] Set up HTTPS with Let's Encrypt
- [ ] Build a CI/CD pipeline with GitHub Actions
- [ ] Manage environment-specific configuration
- [ ] Deploy database migrations safely
- [ ] Plan zero-downtime deployments
- [ ] Monitor production health and performance
