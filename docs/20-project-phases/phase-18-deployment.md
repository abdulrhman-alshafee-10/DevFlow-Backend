# Phase 18 — Deployment

## Objective

Prepare DevFlow for production deployment. Set up Nginx as a reverse proxy, configure HTTPS, build a CI/CD pipeline with GitHub Actions, implement structured logging, and create a production deployment strategy.

---

## Concepts Learned

- Nginx configuration for reverse proxy
- HTTPS with TLS certificates
- CI/CD pipeline design
- Environment management (dev, staging, production)
- Database migration strategy for production
- Production monitoring and health checks
- Graceful deployments
- Structured logging in production

**Relevant docs**:
- `19-deployment/deployment.md`
- `17-observability/observability.md`

---

## Features After This Phase

- [ ] Nginx reverse proxy with TLS termination
- [ ] HTTPS enforced with HSTS
- [ ] CI/CD pipeline (lint → test → build → deploy)
- [ ] Environment-specific configuration (dev, staging, prod)
- [ ] Structured JSON logging in production
- [ ] Database migration as part of deployment
- [ ] Health check monitoring
- [ ] Graceful shutdown and zero-downtime deployment plan

---

## CI/CD Pipeline (GitHub Actions)

```
Trigger: Push to main branch

Jobs:
1. Lint & Type Check
   - ruff check .
   - mypy .

2. Test
   - Start test services (PostgreSQL, Redis)
   - Run migrations
   - pytest --cov

3. Build
   - Build Docker image
   - Tag with commit SHA and "latest"
   - Push to container registry

4. Deploy to Staging
   - Pull new image
   - Run migrations
   - Restart services
   - Run smoke tests

5. Deploy to Production (manual approval)
   - Backup database
   - Pull new image
   - Run migrations
   - Rolling restart
   - Verify health checks
```

---

## Nginx Configuration

```
upstream app {
    server app:8000;
}

server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    
    ssl_certificate /etc/letsencrypt/live/.../fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/.../privkey.pem;
    
    location /api/ {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Request-ID $request_id;
    }
    
    location /ws/ {
        proxy_pass http://app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Completion Checklist

- [ ] Created Nginx configuration with TLS support
- [ ] Created `docker-compose.prod.yml` with Nginx
- [ ] Created GitHub Actions CI/CD workflow
- [ ] CI pipeline runs linting, type checking, and tests
- [ ] Docker images built and pushed to registry
- [ ] Environment configuration for dev/staging/prod
- [ ] Structured logging configured for production
- [ ] Database migration step in deployment pipeline
- [ ] Health check monitoring set up
- [ ] Deployment documentation written
- [ ] Rollback procedure documented and tested
- [ ] Production deployment verified end-to-end
