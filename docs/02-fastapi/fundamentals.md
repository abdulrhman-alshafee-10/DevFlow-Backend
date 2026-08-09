# FastAPI Fundamentals

## 1. What Is It?

FastAPI is a modern, high-performance Python web framework for building APIs. It's built on top of **Starlette** (for the web server parts) and **Pydantic** (for data validation). FastAPI combines the best ideas from Flask, Django REST Framework, and API Star into a framework that's fast, type-safe, and developer-friendly.

---

## 2. Why Does It Matter?

- **Performance**: FastAPI is one of the fastest Python frameworks, on par with Node.js and Go for I/O-bound workloads
- **Type safety**: Catches errors at development time through Pydantic validation
- **Automatic documentation**: Generates OpenAPI (Swagger) and ReDoc documentation from your code
- **Modern Python**: Leverages async/await, type hints, and dataclasses
- **Developer experience**: Excellent error messages, editor auto-complete, and minimal boilerplate

---

## 3. When Should I Use It?

- **RESTful APIs** — The primary use case
- **Microservices** — Lightweight, fast startup
- **Real-time applications** — Built-in WebSocket support
- **ML/AI serving** — Popular for serving ML models due to performance and Pydantic validation
- **Data-intensive applications** — Async I/O handles high concurrency well

---

## 4. When Should I NOT Use It?

- **Server-rendered HTML applications** — Django or Flask with templates are better suited
- **When you need a batteries-included framework** — Django includes admin, ORM, auth, etc. out of the box
- **When your team knows Django well** — The best framework is the one your team knows
- **Simple scripts** — Flask might be simpler for tiny projects

---

## 5. How Does It Work?

### Application Creation

A FastAPI application is an instance of the `FastAPI` class. You create it, register routes, middleware, and exception handlers, then serve it with an ASGI server (Uvicorn).

### Request Lifecycle

```
Client Request
    ↓
Uvicorn (ASGI Server)
    ↓
Middleware Stack (each middleware can modify request/response)
    ↓
Route Matching (find the matching path operation)
    ↓
Dependency Resolution (resolve all Depends() in order)
    ↓
Request Validation (Pydantic validates path, query, body)
    ↓
Endpoint Function (your code runs)
    ↓
Response Serialization (Pydantic serializes the response)
    ↓
Middleware Stack (response passes back through middleware)
    ↓
Client Response
```

### Key Concepts

- **Path Operations**: Functions decorated with `@app.get()`, `@app.post()`, etc.
- **Path Parameters**: Dynamic URL segments (`/users/{user_id}`)
- **Query Parameters**: URL parameters (`?page=1&size=10`)
- **Request Body**: JSON data validated by Pydantic models
- **Response Model**: Controls what data is returned to the client
- **Dependencies**: Injectable functions that provide shared logic
- **Middleware**: Functions that process every request/response

---

## 6. How Does It Fit Into DevFlow?

The FastAPI application is the heart of DevFlow. It:

- **Serves the REST API** — All CRUD operations for users, organizations, projects, tasks
- **Handles WebSocket connections** — Real-time chat and notifications
- **Streams SSE responses** — AI response streaming, live updates
- **Manages authentication** — JWT validation on every request
- **Enforces authorization** — Permission checks via dependencies
- **Generates API documentation** — Interactive Swagger UI for development and testing

---

## 7. Common Mistakes

### Not Understanding the Difference Between `def` and `async def`

- `async def` endpoints run on the event loop — use for I/O operations
- `def` endpoints run in a thread pool — use for CPU-bound or sync library code
- Using `def` for database operations blocks a thread; using `async def` with sync I/O blocks the event loop

### Putting Business Logic in Endpoints

Endpoints should be thin — validate input, call a service, return a response. Business logic belongs in the service layer.

### Not Using `response_model`

Without a response model, your endpoint might accidentally expose sensitive fields (like password hashes).

### Ignoring the Auto-Generated Documentation

FastAPI's Swagger UI (`/docs`) is your best friend for testing and debugging.

---

## 8. Production Considerations

- **Run with Gunicorn + Uvicorn workers** — Multiple worker processes for reliability
- **Disable Swagger in production** — Or protect it with authentication
- **Configure CORS properly** — Restrict allowed origins
- **Set up structured logging** — FastAPI's default logging is minimal
- **Use lifespan events** — Properly initialize and clean up resources (database pools, Redis connections)
- **Monitor performance** — Track response times, error rates, and throughput

---

## 9. Prerequisites

- Python basics (functions, classes, modules)
- Async/await (see `01-python/async-await.md`)
- Type hints (see `01-python/typing.md`)
- HTTP basics (methods, status codes, headers)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Create a FastAPI application
- [ ] Define path operations with different HTTP methods
- [ ] Run the application with Uvicorn
- [ ] Access the auto-generated Swagger UI
- [ ] Understand the request lifecycle
- [ ] Know the difference between `def` and `async def` endpoints
