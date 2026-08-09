# FastAPI Lifespan Events

## 1. What Is It?

Lifespan events are hooks that run when your FastAPI application starts up and shuts down. They allow you to initialize resources (database connections, Redis pools, background workers) when the app starts and clean them up when it stops.

---

## 2. Why Does It Matter?

Production applications need resources that are expensive to create and must be shared across requests:

- **Database connection pools** — Creating a new database connection per request is too slow
- **Redis connections** — Same issue as database connections
- **HTTP client sessions** — For calling external APIs (AI services)
- **Background worker connections** — For dispatching background jobs

Lifespan events ensure these resources are created once at startup and properly closed at shutdown.

---

## 3. When Should I Use It?

- **Database pool initialization** — Create the async engine and session factory
- **Redis connection** — Initialize the Redis client
- **HTTP client** — Create an `httpx.AsyncClient` for external API calls
- **Background workers** — Start background task consumers
- **Cache warming** — Pre-populate frequently accessed data
- **Health check registration** — Register with a service registry

---

## 4. When Should I NOT Use It?

- **Request-specific resources** — Use dependencies with `yield` instead
- **One-off scripts** — Lifespan is for the application lifecycle, not one-time operations
- **Per-user resources** — These should be created per request, not at startup

---

## 5. How Does It Work?

### Modern Approach: `lifespan` Context Manager

FastAPI's recommended approach uses an async context manager with `asynccontextmanager`. The code before `yield` runs at startup, and the code after `yield` runs at shutdown.

### State Management

The lifespan function can store resources in `app.state`, making them accessible throughout the application via `request.app.state`.

### Startup/Shutdown Sequence

```
Application Start
    ↓
Lifespan: before yield
    ├── Create database engine
    ├── Create Redis connection
    ├── Create HTTP client
    └── Run initial migrations (optional)
    ↓
Application Running (handling requests)
    ↓
Application Stop (SIGTERM/SIGINT)
    ↓
Lifespan: after yield
    ├── Close HTTP client
    ├── Close Redis connection
    ├── Dispose database engine
    └── Wait for in-flight requests
    ↓
Application Stopped
```

---

## 6. How Does It Fit Into DevFlow?

DevFlow's lifespan initializes:

1. **Database engine** — Async SQLAlchemy engine with connection pool
2. **Redis client** — For caching, rate limiting, and pub/sub
3. **HTTP client** — For AI API calls (OpenAI, Anthropic)
4. **Background worker connection** — For dispatching Celery/ARQ tasks

At shutdown:
1. Close the HTTP client (wait for in-flight AI requests)
2. Close Redis connections
3. Dispose of the database engine (wait for queries to complete)

---

## 7. Common Mistakes

### Using Deprecated `on_event` Decorator

The `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators are deprecated. Use the `lifespan` context manager instead.

### Not Handling Startup Failures

If the database is unavailable at startup, the app should fail fast with a clear error, not start and crash on the first request.

### Not Waiting for Cleanup

Calling `engine.dispose()` without waiting for pending queries can corrupt data. Always use `await` properly.

### Storing Global State in Modules

Don't use module-level variables for shared resources. Use `app.state` or a proper DI container.

---

## 8. Production Considerations

- **Graceful shutdown** — Wait for in-flight requests before closing connections
- **Health checks** — Only report healthy after all resources are initialized
- **Timeouts** — Set startup timeouts so a hung database connection doesn't block deployment
- **Signal handling** — Uvicorn handles SIGTERM; your lifespan cleanup runs automatically
- **Multiple workers** — Each worker process runs its own lifespan; ensure your resources handle this

---

## 9. Prerequisites

- FastAPI fundamentals
- Async context managers (`async with`)
- Understanding of connection pools

---

## 10. What I Should Be Able to Do Afterward

- [ ] Implement lifespan with the async context manager pattern
- [ ] Initialize and clean up database, Redis, and HTTP client connections
- [ ] Store shared resources in `app.state`
- [ ] Handle startup failures gracefully
- [ ] Understand the difference between lifespan and per-request resources
