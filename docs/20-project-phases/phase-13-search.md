# Phase 13 — Search

## Objective

Implement full-text search across tasks, projects, and comments using PostgreSQL's built-in search capabilities. Provide a unified search API with ranking, highlighting, and filtering.

---

## Concepts Learned

- PostgreSQL full-text search (tsvector, tsquery, GIN index)
- Search ranking and relevance
- Search highlighting
- Multi-entity search (tasks + projects + comments)
- Search indexing strategies
- Search API design

**Relevant docs**:
- `13-search/postgres-search.md`

---

## Features After This Phase

- [ ] Search tasks by title and description
- [ ] Search projects by name and description
- [ ] Search comments by content
- [ ] Unified search endpoint returning mixed results
- [ ] Results ranked by relevance
- [ ] Search within organization scope
- [ ] Filter search by entity type
- [ ] Highlighting of matching terms in results

---

## Database Changes

### Add Search Vectors

```
ALTER TABLE tasks ADD COLUMN search_vector tsvector;
CREATE INDEX idx_tasks_search ON tasks USING GIN(search_vector);
CREATE TRIGGER tasks_search_update BEFORE INSERT OR UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION
  tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description);

ALTER TABLE projects ADD COLUMN search_vector tsvector;
CREATE INDEX idx_projects_search ON projects USING GIN(search_vector);

ALTER TABLE comments ADD COLUMN search_vector tsvector;
CREATE INDEX idx_comments_search ON comments USING GIN(search_vector);
```

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/search` | Unified search | Yes |
| GET | `/api/v1/search/tasks` | Search tasks only | Yes |
| GET | `/api/v1/search/projects` | Search projects only | Yes |

### Search Parameters

```
GET /api/v1/search?q=login+bug&type=task&project_id=uuid&page=1&size=20
```

### Search Response

```json
{
  "results": [
    {
      "type": "task",
      "id": "...",
      "title": "Fix <mark>login</mark> <mark>bug</mark>",
      "snippet": "Users report a <mark>login</mark> <mark>bug</mark> on mobile...",
      "rank": 0.85,
      "project_name": "Mobile App",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "size": 20
}
```

---

## Completion Checklist

- [ ] Added search_vector columns and GIN indexes via migration
- [ ] Created triggers to update search vectors on insert/update
- [ ] Backfilled search vectors for existing data
- [ ] Created search repository with ranking and highlighting
- [ ] Created search service with authorization (org-scoped)
- [ ] Created unified search endpoint
- [ ] Search results are properly ranked
- [ ] Highlighting works in results
- [ ] Search respects organization boundaries
- [ ] Performance tested with realistic data volume
