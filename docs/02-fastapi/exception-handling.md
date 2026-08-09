# Exception Handling in FastAPI

## 1. What Is It?

Exception handling in FastAPI is the mechanism for converting Python exceptions into structured HTTP error responses. FastAPI provides built-in exception handlers and allows you to define custom handlers for your own exception types.

---

## 2. Why Does It Matter?

Without proper exception handling:
- Unhandled exceptions return generic 500 errors with no useful information
- Different errors return inconsistent response formats
- Internal details (stack traces, database errors) leak to clients
- It's impossible to distinguish between different types of errors programmatically

With proper exception handling:
- Every error returns a consistent, structured JSON response
- The client can programmatically determine what went wrong
- Sensitive details are logged but never exposed
- Error codes enable localization and client-side error handling

---

## 3. When Should I Use It?

- **Always** — Every API needs consistent error handling
- **Custom exception classes** — For domain-specific errors (not found, forbidden, conflict)
- **Global exception handlers** — For catching unhandled exceptions
- **Validation error customization** — For reformatting Pydantic validation errors

---

## 4. When Should I NOT Use It?

- **Don't use exceptions for flow control** — If something is expected (e.g., empty search results), return an empty list, don't raise an exception
- **Don't catch and re-raise without adding value** — If you can't handle it meaningfully, let it propagate

---

## 5. How Does It Work?

### FastAPI's Built-In Exception Handling

FastAPI provides `HTTPException` for raising HTTP errors and `RequestValidationError` for invalid request data. You register custom handlers with `@app.exception_handler()`.

### Error Response Structure

A consistent error format for DevFlow:

```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID 123 was not found",
    "details": null,
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "abc-123-def"
  }
}
```

### Exception Handler Registration

Register handlers for each custom exception type. Each handler converts the exception into the appropriate HTTP response with the correct status code and error body.

---

## 6. How Does It Fit Into DevFlow?

DevFlow maps domain exceptions to HTTP responses:

| Exception | HTTP Status | Error Code |
|---|---|---|
| `NotFoundError` | 404 | `RESOURCE_NOT_FOUND` |
| `InvalidCredentialsError` | 401 | `INVALID_CREDENTIALS` |
| `TokenExpiredError` | 401 | `TOKEN_EXPIRED` |
| `InsufficientPermissionsError` | 403 | `INSUFFICIENT_PERMISSIONS` |
| `DuplicateEmailError` | 409 | `DUPLICATE_EMAIL` |
| `BusinessRuleViolationError` | 422 | `BUSINESS_RULE_VIOLATION` |
| `RateLimitExceededError` | 429 | `RATE_LIMIT_EXCEEDED` |
| `ExternalServiceError` | 502 | `EXTERNAL_SERVICE_ERROR` |
| Unhandled `Exception` | 500 | `INTERNAL_SERVER_ERROR` |

---

## 7. Common Mistakes

### Inconsistent Error Formats

Some endpoints returning `{"detail": "..."}`, others returning `{"error": "..."}`, others returning `{"message": "..."}`. Pick one format and use it everywhere.

### Exposing Internal Errors

Never return database error messages, stack traces, or file paths to the client. Log them; return a generic message.

### Not Handling Validation Errors

Pydantic's default validation error format is verbose. Customize it to match your error format.

### Catching Too Broadly

`except Exception:` at the endpoint level hides bugs. Let exceptions propagate to your global handlers.

---

## 8. Production Considerations

- **Log all 5xx errors** with full stack traces
- **Monitor error rates** by error code
- **Include request IDs** in error responses for support debugging
- **Sanitize error messages** — No SQL queries, file paths, or internal details
- **Rate-limit error responses** — Prevent information leakage through error enumeration

---

## 9. Prerequisites

- Python exceptions (see `01-python/exceptions.md`)
- FastAPI fundamentals
- HTTP status codes

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define custom exception classes for a web API
- [ ] Register exception handlers in FastAPI
- [ ] Return consistent error responses across all endpoints
- [ ] Customize Pydantic validation error responses
- [ ] Log errors without exposing sensitive information
- [ ] Map domain exceptions to appropriate HTTP status codes
