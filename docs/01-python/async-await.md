# Async/Await in Python

## 1. What Is It?

`async` and `await` are Python keywords that enable **asynchronous programming** — a way to write code that can handle multiple operations concurrently without using threads.

An `async` function (coroutine) can pause execution at `await` points, allowing other coroutines to run during that time. This is particularly powerful for **I/O-bound operations** like database queries, HTTP requests, and file operations.

```
Traditional (synchronous):     Async:
Task A: ████████               Task A: ██░░░░██
Task B:         ████████       Task B:   ████
Task C:                 ████   Task C:       ████
Time:   ──────────────────→    Time:   ──────────→
```

---

## 2. Why Does It Matter?

FastAPI is built on **ASGI (Asynchronous Server Gateway Interface)**, which means it's designed from the ground up to handle async operations. Understanding async/await is not optional — it's fundamental to writing effective FastAPI code.

**Performance implications**:
- A synchronous endpoint that makes a 100ms database query blocks the worker for 100ms
- An async endpoint releases the worker during that 100ms to handle other requests
- Under load, this difference means serving 10x–100x more concurrent requests

**In DevFlow**: Nearly every request will involve I/O — database queries, Redis lookups, external API calls (AI), email sending. Making these async means DevFlow can handle many concurrent users efficiently.

---

## 3. When Should I Use It?

- **Database queries** — Every SQLAlchemy query in DevFlow
- **Redis operations** — Cache reads/writes, rate limit checks
- **HTTP requests** — Calling external APIs (AI services, OAuth providers)
- **File operations** — Reading/writing files to storage
- **Email sending** — SMTP operations
- **WebSocket handling** — Real-time communication
- **Any I/O-bound operation** — Anything that waits for an external system

---

## 4. When Should I NOT Use It?

- **CPU-bound operations** — Heavy computation (image processing, data crunching). Async won't help here; use `run_in_executor()` or a background worker instead
- **Simple synchronous libraries** — If a library doesn't support async, wrapping it in `async` adds overhead without benefit
- **Trivial operations** — If a function just does in-memory computation, making it async adds unnecessary complexity
- **When you need true parallelism** — Async is concurrent, not parallel. For CPU parallelism, use multiprocessing

---

## 5. How Does It Work?

### The Event Loop

At the heart of async Python is the **event loop** — a single-threaded loop that manages coroutines:

1. The event loop picks a coroutine to run
2. The coroutine runs until it hits an `await`
3. The event loop suspends that coroutine and picks another
4. When the awaited operation completes, the coroutine is resumed

### Key Concepts

- **Coroutine**: A function defined with `async def`. Calling it returns a coroutine object, not the result
- **Awaitable**: Anything you can use `await` on — coroutines, tasks, futures
- **Task**: A coroutine wrapped in a Task object so it runs concurrently
- **Event Loop**: The scheduler that manages all async operations

### FastAPI and Async

FastAPI handles the event loop for you. When you define an `async def` endpoint, FastAPI:

1. Receives the HTTP request
2. Calls your async endpoint function
3. The endpoint can `await` database queries, Redis calls, etc.
4. While waiting, other requests are processed
5. When the await completes, your endpoint continues
6. The response is sent back

If you define a regular `def` endpoint (not async), FastAPI runs it in a thread pool to prevent blocking.

---

## 6. How Does It Fit Into DevFlow?

- **Every API endpoint** will be `async def` because they all query the database
- **Database session management** uses async context managers
- **Redis operations** use `aioredis` (async Redis client)
- **AI API calls** use `httpx.AsyncClient` for non-blocking external requests
- **WebSocket handlers** are inherently async
- **Background task dispatching** is async
- **Email sending** uses async SMTP clients

Example of where async matters in DevFlow: When a user creates a task, the endpoint needs to:
1. Query the database to verify the project exists
2. Check Redis for cached permissions
3. Insert the task into the database
4. Send a notification via Redis pub/sub
5. Enqueue a background job for email notification

All 5 operations involve I/O. With async, the server can handle other requests during each wait.

---

## 7. Common Mistakes

### Blocking the Event Loop

The most dangerous mistake — calling synchronous I/O in an async function:

```
# BAD: This blocks the entire event loop
async def get_data():
    result = requests.get("https://api.example.com")  # Sync HTTP call!
    return result

# GOOD: Use an async HTTP client
async def get_data():
    async with httpx.AsyncClient() as client:
        result = await client.get("https://api.example.com")
    return result
```

### Forgetting to `await`

If you forget `await`, you get a coroutine object instead of the result. Python will warn you, but it's easy to miss.

### Using `async def` When Not Needed

Making a function `async` when it does no I/O adds a tiny overhead and confuses readers. Keep synchronous functions synchronous.

### Mixing Sync and Async Database Drivers

Using a synchronous database driver (like `psycopg2`) with async SQLAlchemy negates all async benefits. Use `asyncpg` instead.

### Not Understanding `asyncio.gather()`

When you need multiple independent I/O operations, run them concurrently:

```
# SLOW: Sequential
result_a = await fetch_a()
result_b = await fetch_b()

# FAST: Concurrent
result_a, result_b = await asyncio.gather(fetch_a(), fetch_b())
```

---

## 8. Production Considerations

- **Event loop monitoring** — In production, monitor event loop lag to detect blocking calls
- **Timeouts** — Always set timeouts on async operations to prevent hanging connections
- **Connection pooling** — Async database connections should use a pool (SQLAlchemy handles this)
- **Graceful shutdown** — On shutdown, wait for in-flight coroutines to complete
- **Worker count** — Uvicorn with multiple workers (via Gunicorn) provides both async concurrency and process-level parallelism
- **Resource limits** — Even async has limits; you can exhaust database connections or memory if you don't manage concurrency

---

## 9. Prerequisites

- Basic Python (functions, classes, modules)
- Understanding of I/O operations (network, file, database)
- Basic understanding of concurrency vs. parallelism (helpful, not required)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define async functions and use `await` correctly
- [ ] Explain why async is important for web servers
- [ ] Identify blocking calls in async code
- [ ] Use `asyncio.gather()` for concurrent operations
- [ ] Understand when async helps and when it doesn't
- [ ] Explain the event loop at a high level
- [ ] Write async FastAPI endpoints that query a database
