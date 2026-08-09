# Python Exceptions

## 1. What Is It?

Exceptions are Python's mechanism for handling errors and exceptional conditions. When something goes wrong — a file isn't found, a network request fails, a user provides invalid data — Python raises an exception. You can catch exceptions to handle errors gracefully, or define custom exceptions to represent domain-specific errors.

---

## 2. Why Does It Matter?

In a web API, errors are not exceptional — they're expected. Users will send invalid data, try to access resources they don't own, and request things that don't exist. A well-designed exception system:

- **Separates error handling from business logic** — Your service layer raises exceptions; your API layer converts them to HTTP responses
- **Provides consistent error responses** — Every error follows the same format
- **Enables global error handling** — FastAPI's exception handlers catch errors in one place
- **Improves debugging** — Custom exceptions carry context about what went wrong

---

## 3. When Should I Use It?

- **Input validation failures** — When data doesn't meet business rules
- **Resource not found** — When a requested entity doesn't exist
- **Authorization failures** — When a user lacks permission
- **External service failures** — When a database query or API call fails
- **Business rule violations** — When an operation violates domain rules
- **Conflict states** — When an operation would create an inconsistent state

---

## 4. When Should I NOT Use It?

- **Flow control** — Don't use exceptions for normal program flow (e.g., checking if a list is empty)
- **Expected conditions** — If something is expected to happen frequently, handle it with conditionals, not exceptions
- **Silencing errors** — Never use bare `except:` or `except Exception:` without handling or re-raising

---

## 5. How Does It Work?

### Exception Hierarchy

Python has a built-in exception hierarchy:

```
BaseException
├── SystemExit
├── KeyboardInterrupt
└── Exception
    ├── ValueError
    ├── TypeError
    ├── KeyError
    ├── HTTPException (FastAPI)
    └── YourCustomExceptions
```

### Custom Exception Pattern for APIs

The recommended pattern for FastAPI projects is:

1. Define a base application exception
2. Create specific exceptions for different error categories
3. Map exceptions to HTTP responses using exception handlers

### Exception Hierarchy for DevFlow

```
DevFlowException (base)
├── NotFoundError
│   ├── UserNotFoundError
│   ├── ProjectNotFoundError
│   └── TaskNotFoundError
├── AuthenticationError
│   ├── InvalidCredentialsError
│   ├── TokenExpiredError
│   └── InvalidTokenError
├── AuthorizationError
│   ├── InsufficientPermissionsError
│   └── ResourceAccessDeniedError
├── ConflictError
│   ├── DuplicateEmailError
│   └── DuplicateUsernameError
├── ValidationError
│   └── BusinessRuleViolationError
└── ExternalServiceError
    ├── DatabaseError
    ├── RedisError
    └── AIServiceError
```

---

## 6. How Does It Fit Into DevFlow?

DevFlow uses a layered exception strategy:

- **Repository layer** raises `NotFoundError` when a query returns no results
- **Service layer** raises `AuthorizationError`, `ConflictError`, or `ValidationError` based on business rules
- **API layer** has exception handlers that convert these to proper HTTP responses:
  - `NotFoundError` → 404
  - `AuthenticationError` → 401
  - `AuthorizationError` → 403
  - `ConflictError` → 409
  - `ValidationError` → 422

This separation means your service layer never needs to know about HTTP status codes.

---

## 7. Common Mistakes

### Raising `HTTPException` in the Service Layer

The service layer shouldn't know about HTTP. Raise domain exceptions and let the API layer convert them.

### Catching Too Broadly

`except Exception:` catches everything, hiding bugs. Catch specific exceptions.

### Not Including Context

Exceptions should carry information about what went wrong: which resource wasn't found, which field was invalid, what permission was missing.

### Swallowing Exceptions

Catching an exception and doing nothing (`pass`) hides errors. At minimum, log them.

### Not Using Exception Groups (Python 3.11+)

When multiple errors occur simultaneously (like validating multiple fields), `ExceptionGroup` lets you report all of them.

---

## 8. Production Considerations

- **Never expose internal details** — Stack traces, database errors, and file paths should not reach the client
- **Log exceptions with context** — Include request ID, user ID, and relevant data
- **Use structured error responses** — Consistent JSON format for all errors
- **Monitor exception rates** — Track error frequency to catch regressions
- **Differentiate client vs. server errors** — 4xx errors are client problems; 5xx are your problems

---

## 9. Prerequisites

- Basic Python (try/except/finally)
- Understanding of Python classes and inheritance

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define a custom exception hierarchy for a web application
- [ ] Map domain exceptions to HTTP status codes
- [ ] Write FastAPI exception handlers
- [ ] Include context information in exceptions
- [ ] Handle exceptions at the appropriate layer
- [ ] Log exceptions properly without exposing sensitive data
- [ ] Use exception chaining (`raise ... from ...`)
