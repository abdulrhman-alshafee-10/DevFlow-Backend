# Python Decorators

## 1. What Is It?

A decorator is a function that takes another function (or class) as input and returns a modified version of it. Decorators allow you to add behavior to functions without changing their code — a powerful pattern for cross-cutting concerns like logging, authentication, caching, and validation.

The `@decorator` syntax is syntactic sugar:

```
@my_decorator
def my_function():
    ...

# Is equivalent to:
def my_function():
    ...
my_function = my_decorator(my_function)
```

---

## 2. Why Does It Matter?

Decorators are used extensively in FastAPI and the Python ecosystem:

- **`@app.get("/path")`** — FastAPI's route decorator
- **`@app.middleware("http")`** — Middleware registration
- **`@app.exception_handler(Exception)`** — Exception handler registration
- **`@property`** — Computed attributes in models
- **`@staticmethod`, `@classmethod`** — Method types
- **`@functools.lru_cache`** — Memoization
- **`@pytest.fixture`** — Test fixtures

Understanding how decorators work helps you read FastAPI's source code and write your own reusable patterns.

---

## 3. When Should I Use It?

- **Cross-cutting concerns** — Logging, timing, authentication
- **Registration patterns** — Registering routes, event handlers, plugins
- **Caching** — Memoizing expensive function results
- **Validation** — Checking preconditions before function execution
- **Retry logic** — Automatically retrying failed operations
- **Rate limiting** — Controlling function call frequency

---

## 4. When Should I NOT Use It?

- **When dependency injection is clearer** — FastAPI's `Depends()` is often more readable than a custom decorator for auth/permissions
- **When the logic is one-off** — If you're only applying the behavior once, a decorator adds unnecessary abstraction
- **When it obscures control flow** — Multiple stacked decorators can make code hard to follow
- **When async/sync mixing gets confusing** — Decorating async functions requires careful handling

---

## 5. How Does It Work?

### Simple Decorator

A decorator wraps a function, adding behavior before and/or after:

```
def log_calls(func):
    @functools.wraps(func)     # Preserves original function metadata
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper
```

### Decorators with Arguments

To pass arguments to a decorator, you need a decorator factory — a function that returns a decorator:

```
def retry(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator
```

### Async Decorators

When decorating async functions, the wrapper must also be async:

```
def timing(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.3f}s")
        return result
    return wrapper
```

---

## 6. How Does It Fit Into DevFlow?

While FastAPI's dependency injection system (`Depends()`) handles most cross-cutting concerns, decorators are still useful in DevFlow for:

- **Route registration** — `@router.get()`, `@router.post()`, etc.
- **Retry logic** — Decorating external API calls (AI service) with automatic retries
- **Caching** — `@cached(ttl=60)` for expensive computations
- **Audit logging** — Recording who did what and when
- **Event handlers** — `@app.on_event("startup")` (or lifespan pattern)

In practice, you'll use existing decorators much more often than writing your own. But understanding how they work is essential for reading FastAPI's internals and third-party libraries.

---

## 7. Common Mistakes

### Forgetting `@functools.wraps`

Without it, the wrapped function loses its name, docstring, and other metadata. This breaks FastAPI's introspection.

### Not Handling Async Properly

If you decorate an async function with a sync wrapper, you'll get a coroutine object instead of the result.

### Too Many Stacked Decorators

More than 2-3 decorators on a function is a code smell. Consider refactoring.

### Using Decorators When `Depends()` Is More Appropriate

For authentication, permissions, and database access, FastAPI's dependency injection is more idiomatic and testable.

---

## 8. Production Considerations

- **Performance** — Decorators add a function call overhead. For hot paths, ensure this is negligible
- **Debugging** — Stack traces through decorated functions can be harder to read. `@functools.wraps` helps
- **Testing** — Decorators should be testable independently from the functions they wrap
- **Thread/async safety** — Ensure decorators don't introduce shared mutable state

---

## 9. Prerequisites

- Python functions as first-class objects
- `*args` and `**kwargs`
- Closures (functions returning functions)
- Basic understanding of async/await (for async decorators)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain how the `@decorator` syntax works
- [ ] Write a simple decorator with `@functools.wraps`
- [ ] Write a decorator factory (decorator with arguments)
- [ ] Write an async-compatible decorator
- [ ] Understand FastAPI's route decorators
- [ ] Know when to use decorators vs. `Depends()`
