# Pagination

## 1. What Is It?

Pagination divides large datasets into smaller pages, returned one at a time. Instead of returning 10,000 tasks at once, you return 20 per page with metadata about the total count and next page.

---

## 2. Why Does It Matter?

Without pagination:
- Large responses consume excessive bandwidth and memory
- Client rendering becomes slow
- Database queries are expensive (fetching all rows)
- Time-to-first-byte increases

---

## 5. How Does It Work?

### Offset-Based Pagination

```
GET /tasks?page=1&size=20     → rows 1-20
GET /tasks?page=2&size=20     → rows 21-40
```

**Pros**: Simple, supports jumping to any page
**Cons**: Performance degrades on large offsets (OFFSET 10000 still reads 10000 rows); inconsistent results if data changes between pages

### Cursor-Based Pagination

```
GET /tasks?cursor=abc&size=20  → 20 tasks after the cursor
```

The cursor is an encoded value (usually the last item's ID or timestamp).

**Pros**: Consistent results, fast for any page
**Cons**: Can't jump to page N, must iterate forward

### DevFlow Pagination Response

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 20,
  "pages": 8,
  "has_next": true,
  "has_prev": false
}
```

**DevFlow recommendation**: Start with offset-based pagination (simpler). Switch to cursor-based for infinite scroll or very large datasets.

---

## What I Should Be Able to Do Afterward

- [ ] Implement offset-based pagination
- [ ] Implement cursor-based pagination
- [ ] Create a reusable pagination dependency
- [ ] Return proper pagination metadata
- [ ] Choose the right pagination strategy for each use case
