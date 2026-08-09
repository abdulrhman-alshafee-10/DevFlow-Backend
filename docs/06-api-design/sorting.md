# Sorting

## 1. What Is It?

Sorting allows API clients to control the order of returned results. Instead of always returning tasks in creation order, clients can sort by due date, priority, status, or any other relevant field.

---

## 2. Why Does It Matter?

Different views of the same data need different orderings:
- **Kanban board** → Sort by position within a status column
- **Task list** → Sort by due date (upcoming first)
- **Priority view** → Sort by priority (critical first)
- **Recent activity** → Sort by updated_at (newest first)

---

## 5. How Does It Work?

### Query Parameters

```
GET /tasks?sort_by=due_date&sort_order=asc
GET /tasks?sort_by=priority&sort_order=desc
GET /tasks?sort_by=created_at          # Default order: desc
```

### Implementation Rules

1. **Whitelist sortable fields** — Never allow sorting by arbitrary columns
2. **Default sort** — Always have a default (e.g., `created_at desc`)
3. **Secondary sort** — Add `id` as a tiebreaker for stable pagination
4. **Index sorted columns** — Sorting without an index causes a full table scan + sort

### DevFlow Sortable Fields

| Resource | Sortable Fields | Default |
|---|---|---|
| Tasks | created_at, updated_at, due_date, priority, title | created_at desc |
| Projects | name, created_at, updated_at | created_at desc |
| Comments | created_at | created_at asc |
| Notifications | created_at | created_at desc |
| Members | joined_at, role | joined_at asc |

---

## What I Should Be Able to Do Afterward

- [ ] Implement sorting with query parameters
- [ ] Whitelist sortable fields to prevent abuse
- [ ] Add a default sort order
- [ ] Combine sorting with filtering and pagination
- [ ] Ensure sorted columns are indexed
