# Request & Response Handling

## 1. What Is It?

Request handling is how your API receives and validates incoming data. Response handling is how your API formats and returns data to clients. FastAPI uses Pydantic models for both, providing automatic validation, serialization, and documentation.

---

## 2. Why Does It Matter?

The request/response cycle is the core of any API. Getting it right means:

- **Invalid data is rejected before reaching your business logic** — Pydantic validates everything
- **Sensitive data is never accidentally exposed** — Response models control output
- **API documentation is always accurate** — Generated from your models
- **Clients know exactly what to send and expect** — Clear contracts

---

## 3. When Should I Use It?

- **Every endpoint** — Always define request and response schemas
- **Complex validation** — When simple types aren't enough (email format, password strength, date ranges)
- **Nested data** — When request/response contains complex structures
- **Different views** — When different endpoints return different fields of the same entity

---

## 4. When Should I NOT Use It?

- **Simple health checks** — A plain `{"status": "ok"}` doesn't need a model
- **File downloads** — Binary responses use `StreamingResponse` or `FileResponse`, not Pydantic
- **Redirects** — Use `RedirectResponse`

---

## 5. How Does It Work?

### Request Data Sources

FastAPI extracts data from multiple sources:

| Source | How FastAPI Uses It |
|---|---|
| **Path parameters** | Type-hinted function parameters matching `{param}` in the path |
| **Query parameters** | Function parameters not in the path |
| **Request body** | Parameters type-hinted with a Pydantic model |
| **Headers** | Parameters with `Header()` default |
| **Cookies** | Parameters with `Cookie()` default |
| **Form data** | Parameters with `Form()` default |
| **File uploads** | Parameters with `File()` or `UploadFile` |

### Response Handling

FastAPI serializes responses based on:

- `response_model` — The Pydantic model for the response (controls which fields are included)
- `status_code` — HTTP status code (default 200)
- `response_model_exclude_unset` — Omit fields not explicitly set
- `response_model_exclude` — Exclude specific fields

### Schema Patterns for DevFlow

For each entity, you'll typically have multiple schemas:

```
TaskBase         — Shared fields
TaskCreate       — Fields needed to create a task (request body for POST)
TaskUpdate       — Fields that can be updated (request body for PATCH)
TaskResponse     — Fields returned to the client (response model)
TaskListResponse — Paginated list of tasks
TaskDetail       — Detailed view with relationships (comments, attachments)
```

---

## 6. How Does It Fit Into DevFlow?

Every DevFlow endpoint uses structured request/response handling:

- **POST /tasks** — Accepts `TaskCreate`, returns `TaskResponse` with status 201
- **PATCH /tasks/{id}** — Accepts `TaskUpdate` (all fields optional), returns `TaskResponse`
- **GET /tasks** — Returns `PaginatedResponse[TaskResponse]` with filtering/sorting
- **GET /tasks/{id}** — Returns `TaskDetail` with comments and attachments

Error responses are also structured:

```
{
  "detail": "Task not found",
  "error_code": "TASK_NOT_FOUND",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 7. Common Mistakes

### Using the Same Model for Request and Response

Never use the same model for input and output. The request might have `password`; the response must not.

### Not Using `response_model`

Without it, your endpoint might return database model objects that include password hashes and internal IDs.

### Making All Fields Optional in Create Schemas

Required fields should be required. If a task needs a title, `TaskCreate.title` must be `str`, not `str | None`.

### Returning Database Models Directly

Convert SQLAlchemy models to Pydantic schemas before returning. This prevents leaking internal structure and ensures consistent serialization.

### Not Validating Enums

Use `Literal` or Python `Enum` for fields with a fixed set of values (status, priority, role).

---

## 8. Production Considerations

- **Response size** — Paginate lists, don't return all records at once
- **Sensitive data** — Audit response models to ensure they don't expose internal IDs, hashes, or tokens
- **Versioning** — When changing response models, consider backward compatibility
- **Performance** — Use `response_model_exclude_unset` to reduce payload size
- **Validation error format** — Customize Pydantic validation error responses for consistency

---

## 9. Prerequisites

- Pydantic models (type hints, Field, validators)
- HTTP methods and status codes
- JSON data format

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define Pydantic schemas for request validation
- [ ] Use `response_model` to control API output
- [ ] Create different schemas for create, update, and read operations
- [ ] Validate complex data with Pydantic validators
- [ ] Handle form data and file uploads
- [ ] Return appropriate HTTP status codes
- [ ] Design consistent error response formats
