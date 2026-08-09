# HTTP Status Codes

## 1. What Is It?

HTTP status codes are three-digit numbers that indicate the result of an HTTP request. They're grouped into five categories and are a critical part of REST API design.

---

## DevFlow Status Code Reference

### Success (2xx)

| Code | Meaning | When to Use |
|---|---|---|
| **200** | OK | Successful GET, PUT, PATCH |
| **201** | Created | Successful POST that creates a resource |
| **204** | No Content | Successful DELETE (no body returned) |

### Redirection (3xx)

| Code | Meaning | When to Use |
|---|---|---|
| **301** | Moved Permanently | API version permanently moved |
| **302/307** | Redirect | OAuth2 flows |

### Client Error (4xx)

| Code | Meaning | When to Use |
|---|---|---|
| **400** | Bad Request | Malformed JSON, invalid parameters |
| **401** | Unauthorized | Missing or invalid authentication |
| **403** | Forbidden | Authenticated but not authorized |
| **404** | Not Found | Resource doesn't exist |
| **405** | Method Not Allowed | Wrong HTTP method |
| **409** | Conflict | Duplicate email, conflicting state |
| **413** | Payload Too Large | File upload too big |
| **415** | Unsupported Media Type | Wrong content type |
| **422** | Unprocessable Entity | Validation error (Pydantic) |
| **429** | Too Many Requests | Rate limit exceeded |

### Server Error (5xx)

| Code | Meaning | When to Use |
|---|---|---|
| **500** | Internal Server Error | Unhandled exception |
| **502** | Bad Gateway | External service error (AI API down) |
| **503** | Service Unavailable | Maintenance mode |

---

## What I Should Be Able to Do Afterward

- [ ] Choose the correct status code for any operation
- [ ] Distinguish between 400, 401, 403, and 404
- [ ] Explain when to use 201 vs. 200
- [ ] Return 204 for deletions
- [ ] Use 422 for validation errors and 409 for conflicts
