# API Versioning

## 1. What Is It?

API versioning is a strategy for evolving your API without breaking existing clients. When you need to make breaking changes (removing fields, changing response formats), versioned clients continue using the old version while new clients use the new one.

---

## 2. Why Does It Matter?

Once your API has clients, you can't freely change it. Removing a field, renaming a parameter, or changing a response format breaks existing integrations. Versioning lets you evolve the API safely.

---

## Versioning Strategies

| Strategy | Example | Pros | Cons |
|---|---|---|---|
| **URL prefix** | `/api/v1/tasks` | Simple, explicit, cache-friendly | URL pollution |
| **Header** | `Accept: application/vnd.devflow.v1+json` | Clean URLs | Less discoverable |
| **Query parameter** | `/tasks?version=1` | Simple | Easy to forget |

**DevFlow uses URL prefix versioning** (`/api/v1/`) because it's the most common, most explicit, and easiest to implement.

### When to Create v2

- Removing a required field from a response
- Changing a field's type (string → object)
- Fundamentally changing the endpoint's behavior

### When NOT to Create v2

- Adding a new optional field to a response (backward compatible)
- Adding a new endpoint
- Adding optional query parameters

---

## What I Should Be Able to Do Afterward

- [ ] Implement URL-prefix API versioning
- [ ] Determine when a change requires a new version
- [ ] Maintain multiple API versions simultaneously
- [ ] Deprecate old API versions gracefully
