# Observability — Logging, Tracing, Metrics, and Health Checks

## Structured Logging

### What Is It?
Structured logging outputs log entries as JSON objects instead of plain text. This makes logs machine-parseable, searchable, and filterable.

### Why It Matters
Plain text logs: `2024-01-15 10:30:00 INFO User 123 logged in`
Structured logs:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "User logged in",
  "user_id": "123",
  "ip": "192.168.1.1",
  "request_id": "abc-123",
  "duration_ms": 45
}
```

### DevFlow Logging Strategy
- Use `structlog` for structured JSON logging
- Include `request_id` (correlation ID) in every log entry
- Log: request start/end, authentication events, authorization decisions, errors, external API calls
- **Never log**: passwords, tokens, personal data, credit card numbers

---

## Request Tracing

### What Is It?
Request tracing assigns a unique ID to each request and includes it in all logs, database queries, and external calls. This lets you trace a single request across the entire system.

### Implementation
1. Middleware assigns `X-Request-ID` (or generates one)
2. Store in context variable (Python's `contextvars`)
3. Include in all log entries
4. Pass to external services in headers
5. Return in response headers

---

## Metrics

### What It Tracks
| Metric | Type | Purpose |
|---|---|---|
| Request count | Counter | Traffic volume |
| Request duration | Histogram | Performance |
| Error rate | Counter | Reliability |
| Active connections | Gauge | Load |
| Database query duration | Histogram | DB performance |
| Cache hit rate | Counter | Cache effectiveness |
| Background job queue length | Gauge | Worker health |

### Tools
- **Prometheus** — Metrics collection
- **Grafana** — Visualization and dashboards

---

## Health Checks

### What They Are
Health check endpoints report whether the application is functioning correctly. Used by:
- Load balancers (route traffic away from unhealthy instances)
- Container orchestrators (restart unhealthy containers)
- Monitoring systems (alert when services are down)

### DevFlow Health Endpoints

```
GET /health         → Basic health (app is running)
GET /health/ready   → Readiness (DB connected, Redis connected, dependencies OK)
```

**Basic health** (liveness): Returns 200 if the process is alive.
**Readiness**: Checks all dependencies:
- Database connection works
- Redis connection works
- Required environment variables are set

### Rules
- Health checks must be fast (<100ms)
- Health checks must NOT require authentication
- Health checks must NOT expose sensitive information
- Return 200 for healthy, 503 for unhealthy

---

## What I Should Be Able to Do Afterward

- [ ] Set up structured logging with structlog
- [ ] Implement request correlation IDs
- [ ] Create health check endpoints
- [ ] Understand metrics collection with Prometheus
- [ ] Configure log levels for different environments
- [ ] Never log sensitive data
