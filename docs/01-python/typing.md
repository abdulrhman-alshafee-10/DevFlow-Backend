# Python Type Hints

## 1. What Is It?

Type hints (also called type annotations) are a way to declare the expected types of variables, function parameters, and return values in Python. They were introduced in Python 3.5 (PEP 484) and have become increasingly important in modern Python development.

Type hints don't change how Python runs your code — Python remains dynamically typed. But they enable tools like **mypy** (static type checker), **Pydantic** (runtime validation), and **FastAPI** (automatic request/response handling) to catch errors and generate documentation.

---

## 2. Why Does It Matter?

FastAPI is **built on type hints**. They are not optional — they are the mechanism through which FastAPI:

- **Validates request data** — Path parameters, query parameters, and request bodies are validated based on type hints
- **Serializes response data** — Response models use type hints to control what data is returned
- **Generates documentation** — OpenAPI/Swagger docs are built from type hints
- **Enables auto-complete** — Your IDE can provide intelligent suggestions

Without solid type hint knowledge, you cannot use FastAPI effectively.

---

## 3. When Should I Use It?

- **Always** in FastAPI code — endpoint parameters, Pydantic models, dependency functions
- **Function signatures** — Parameters and return types
- **Class attributes** — Especially SQLAlchemy models and Pydantic schemas
- **Complex data structures** — Lists of objects, optional fields, unions
- **Public APIs** — Any function other developers will call

---

## 4. When Should I NOT Use It?

- **Throwaway scripts** — Quick one-off scripts don't benefit much
- **When types are truly dynamic** — Some metaprogramming patterns resist typing
- **Over-annotating local variables** — If the type is obvious from context, local variable annotations can be noise

---

## 5. How Does It Work?

### Basic Types

```
str, int, float, bool, bytes, None
```

### Collection Types (Python 3.9+)

```
list[str]              # List of strings
dict[str, int]         # Dict with string keys and int values
tuple[str, int]        # Tuple with exactly a string and an int
set[str]               # Set of strings
```

### Optional and Union

```
str | None             # Python 3.10+ union syntax (replaces Optional[str])
int | str              # Can be int or string
Optional[str]          # Same as str | None (from typing module)
```

### Pydantic-Specific Patterns

Pydantic uses type hints for validation:

```
field: str                    → Required string
field: str = "default"        → String with default
field: str | None = None      → Optional string
field: list[str] = []         → List with default empty
field: EmailStr               → Validated email format
field: conint(ge=1, le=100)   → Integer between 1 and 100
```

### Advanced Types

```
Callable[[int, str], bool]    # Function type
Annotated[int, Field(ge=0)]   # Metadata-enhanced type (used heavily in FastAPI)
Literal["active", "archived"] # Specific allowed values
TypeVar, Generic               # For generic classes
```

---

## 6. How Does It Fit Into DevFlow?

Type hints are used everywhere in DevFlow:

- **Pydantic schemas**: Every request and response model uses type hints for validation
- **SQLAlchemy models**: Column types and relationship declarations
- **FastAPI endpoints**: Path parameters, query parameters, request bodies, response models
- **Dependencies**: Function return types tell FastAPI what to inject
- **Service methods**: Parameter and return types for business logic

Examples of DevFlow types you'll define:

- `TaskStatus` as a `Literal["todo", "in_progress", "review", "done"]`
- `TaskPriority` as a `Literal["low", "medium", "high", "critical"]`
- `list[TaskResponse]` for endpoint return types
- `UUID` for all entity IDs
- `datetime` for timestamps
- `Annotated[str, Query(min_length=1)]` for search parameters

---

## 7. Common Mistakes

### Confusing `list` with `List` (from typing)

In Python 3.9+, use lowercase `list[str]` instead of `typing.List[str]`. The old syntax still works but is deprecated.

### Forgetting `| None` for Optional Fields

If a field can be null, you must annotate it. An unannotated field in Pydantic is required.

### Using `dict` When You Need a Model

Instead of `dict[str, Any]` for complex structures, define a Pydantic model. You get validation, documentation, and IDE support.

### Not Using `Annotated` for FastAPI Dependencies

FastAPI v0.95+ recommends `Annotated` for dependencies:

```
# Modern (recommended)
async def endpoint(db: Annotated[AsyncSession, Depends(get_db)]):

# Old style (still works)
async def endpoint(db: AsyncSession = Depends(get_db)):
```

### Circular Import Issues with Type Hints

When models reference each other, use `from __future__ import annotations` or string literal types to avoid circular imports.

---

## 8. Production Considerations

- **Use `mypy` in CI/CD** — Catch type errors before deployment
- **Strict mode** — Consider `mypy --strict` for maximum safety
- **Pydantic v2 performance** — v2 validates types in Rust, so type hints have near-zero runtime overhead
- **Documentation accuracy** — Type hints generate your API docs; incorrect types mean incorrect docs
- **Versioning** — When changing response types, be aware that clients depend on the documented types

---

## 9. Prerequisites

- Basic Python (variables, functions, classes)
- Understanding of Python's dynamic typing

---

## 10. What I Should Be Able to Do Afterward

- [ ] Annotate function parameters and return types
- [ ] Use generic types (`list[str]`, `dict[str, int]`)
- [ ] Use `Optional` / `| None` correctly
- [ ] Define Pydantic models with proper type hints
- [ ] Use `Annotated` for FastAPI dependencies
- [ ] Understand how FastAPI uses type hints for validation
- [ ] Use `Literal` for constrained string values
- [ ] Resolve circular import issues with type hints
