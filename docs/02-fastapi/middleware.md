# FastAPI Middleware

## 1. What Is It?

Middleware is code that runs on **every request** before it reaches your endpoint and on **every response** before it's sent to the client. It sits between the server and your route handlers, intercepting and optionally modifying requests and responses.

---

## 2. Why Does It Matter?

Middleware handles cross-cutting concerns — things that apply to all or most requests:

- **Logging** — Log every request with timing, status code, and correlation ID
- **CORS** — Add cross-origin headers to every response
- **Authentication** — Validate tokens before reaching endpoints (though dependencies are preferred in FastAPI)
- **Rate limiting** — Block excessive requests
- **Error handling** — Catch unhandled exceptions globally
- **Request ID** — Assign a unique ID to every request for tracing

---

## 3. When Should I Use It?

- When the logic applies to **all** (or almost all) requests
- When you need to modify the request before route matching
- When you need to add headers to every response
- When you need to measure total request processing time
- When you need request-scoped context (like a correlation ID)

---

## 4. When Should I NOT Use It?

- **Route-specific logic** — Use dependencies instead
- **Authentication** — Dependencies are more flexible and testable in FastAPI
- **Complex business logic** — Middleware should be simple and fast
- **When you need access to path parameters** — Middleware runs before route matching, so it doesn't have access to parsed path parameters

---

## 5. How Does It Work?

### Middleware Execution Order

Middleware executes in a stack:

```
Request  →  Middleware 1  →  Middleware 2  →  Middleware 3  →  Endpoint
Response ←  Middleware 1  ←  Middleware 2  ←  Middleware 3  ←  Endpoint
```

Each middleware can:
1. Process the request
2. Call the next middleware/endpoint
3. Process the response
4. Return the response

### Types of Middleware in FastAPI

1. **ASGI Middleware** — Standard ASGI protocol, wraps the entire app
2. **HTTP Middleware** — FastAPI's `@app.middleware("http")` decorator
3. **Starlette Middleware Classes** — Class-based, reusable

---

## 6. How Does It Fit Into DevFlow?

DevFlow uses middleware for:

- **Request logging** — Log every request with method, path, status, and duration
- **Correlation ID** — Assign a unique `X-Request-ID` to every request for tracing across logs
- **CORS** — Allow the frontend to make requests from a different origin
- **Rate limiting** — Limit requests per IP/user (can also be done as a dependency)
- **Security headers** — Add `X-Content-Type-Options`, `X-Frame-Options`, etc. to every response
- **Process time header** — Add `X-Process-Time` header for monitoring

---

## 7. Common Mistakes

### Doing Too Much in Middleware

Middleware runs on every request. Heavy computation or I/O slows down everything.

### Not Calling `call_next(request)`

Forgetting to call the next handler means the request is swallowed and the client gets no response.

### Order Dependency Bugs

Middleware order matters. If your logging middleware is added after your CORS middleware, CORS pre-flight requests won't be logged.

### Using Middleware for Route-Specific Logic

If you only need something on a few routes, use dependencies, not middleware.

---

## 8. Production Considerations

- **Performance monitoring** — Track middleware execution time separately from endpoint time
- **Error handling** — Ensure middleware doesn't crash and kill the entire request
- **Security headers** — Apply security headers via middleware in production
- **Request size limits** — Enforce maximum request body size
- **Timeouts** — Add request timeout middleware to prevent hanging connections

---

## 9. Prerequisites

- FastAPI fundamentals
- HTTP request/response cycle
- Async/await

---

## 10. What I Should Be Able to Do Afterward

- [ ] Write custom HTTP middleware with `@app.middleware("http")`
- [ ] Add CORS middleware with proper configuration
- [ ] Implement request logging with timing
- [ ] Add correlation IDs for request tracing
- [ ] Understand middleware execution order
- [ ] Know when to use middleware vs. dependencies
