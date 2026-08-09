# Filtering, Sorting, and Searching

## Filtering

### What Is It?
Filtering allows clients to request a subset of resources matching specific criteria.

### DevFlow Filtering Examples
```
GET /tasks?status=in_progress
GET /tasks?priority=high&assignee_id=uuid
GET /tasks?created_after=2024-01-01&created_before=2024-06-01
GET /tasks?status=todo,in_progress  (multiple values)
```

### Implementation
- Accept filter parameters as query parameters
- Validate values against allowed options (use Pydantic)
- Build dynamic WHERE clauses in the repository layer
- Create a reusable `TaskFilter` dependency class

---

## Sorting

### What Is It?
Sorting allows clients to order results by one or more fields.

### DevFlow Sorting Examples
```
GET /tasks?sort_by=created_at&sort_order=desc
GET /tasks?sort_by=priority&sort_order=asc
GET /tasks?sort_by=due_date     (default: asc)
```

### Implementation
- Whitelist sortable fields (don't allow sorting by arbitrary columns)
- Default sort order: `created_at desc`
- Validate against allowed fields
- Apply ORDER BY in the repository layer

---

## Searching

### What Is It?
Searching allows clients to find resources matching a text query.

### DevFlow Searching Examples
```
GET /tasks?search=login+bug
GET /projects?search=mobile+app
```

### Implementation Stages
1. **Simple LIKE search** — `WHERE title ILIKE '%query%'` (good enough for small datasets)
2. **PostgreSQL full-text search** — `WHERE to_tsvector(title || description) @@ to_tsquery('query')` (better ranking, stemming)
3. **Elasticsearch** — Advanced search with faceting and fuzzy matching (when needed)

---

## Combined Example

```
GET /tasks?project_id=uuid&status=in_progress&priority=high&search=auth&sort_by=due_date&sort_order=asc&page=1&size=20
```

This request: filters tasks by project, status, and priority; searches for "auth" in title/description; sorts by due date; returns page 1 with 20 results.

---

## What I Should Be Able to Do Afterward

- [ ] Implement dynamic filtering with query parameters
- [ ] Validate filter values and whitelist sortable fields
- [ ] Implement text searching with PostgreSQL
- [ ] Combine filtering, sorting, searching, and pagination in a single query
- [ ] Create reusable filter/sort dependency classes
