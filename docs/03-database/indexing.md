# Database Indexing

## 1. What Is It?

A database index is a data structure that improves the speed of data retrieval operations on a table. Like a book's index, it lets the database find specific rows without scanning the entire table. Without an index, PostgreSQL must perform a sequential scan — reading every row to find matches.

---

## 2. Why Does It Matter?

As DevFlow grows, tables like `tasks` will have thousands or millions of rows. Without indexes:

- Listing tasks for a project scans the entire table
- Searching by title requires reading every row
- Sorting by creation date recomputes the order every time
- Each slow query ties up a database connection

Proper indexing can turn a 500ms query into a 5ms query.

---

## 3. When Should I Use It?

- **Columns in WHERE clauses** — `status`, `priority`, `assignee_id`, `project_id`
- **Columns in JOIN conditions** — Foreign keys
- **Columns in ORDER BY** — `created_at`, `due_date`, `priority`
- **Columns in GROUP BY** — For aggregation queries
- **Unique constraints** — `email`, `username` (unique indexes)
- **Full-text search** — GIN indexes on text columns

---

## 4. When Should I NOT Use It?

- **Low-cardinality columns** — A boolean column with only TRUE/FALSE rarely benefits from an index
- **Small tables** — Tables with <1000 rows don't need indexes; sequential scans are fast enough
- **Write-heavy tables** — Every index slows down INSERT/UPDATE/DELETE because the index must be updated too
- **Rarely queried columns** — Don't index a column you never filter or sort by

---

## 5. How Does It Work?

### Index Types in PostgreSQL

| Type | Use Case | Example |
|---|---|---|
| **B-tree** | Default; equality and range queries | `WHERE created_at > '2024-01-01'` |
| **Hash** | Exact equality only | `WHERE id = '...'` (rare; B-tree is usually better) |
| **GIN** | Full-text search, JSONB, arrays | `WHERE to_tsvector(title) @@ to_tsquery('bug')` |
| **GiST** | Geometric data, full-text search | Range types, geographic queries |
| **BRIN** | Very large tables with natural ordering | Time-series data ordered by timestamp |

### Composite Indexes

An index on multiple columns. Column order matters:

```
INDEX ON tasks (project_id, status)
```

This index helps:
- `WHERE project_id = X` ✓
- `WHERE project_id = X AND status = 'active'` ✓
- `WHERE status = 'active'` ✗ (first column not used)

### Partial Indexes

Index only rows matching a condition:

```
INDEX ON tasks (assignee_id) WHERE status != 'done'
```

Smaller, faster, and only indexes active tasks.

---

## 6. How Does It Fit Into DevFlow?

Key indexes for DevFlow:

| Table | Column(s) | Type | Purpose |
|---|---|---|---|
| `users` | `email` | Unique B-tree | Login lookup, uniqueness |
| `tasks` | `project_id` | B-tree | List tasks by project |
| `tasks` | `assignee_id` | B-tree | List tasks by assignee |
| `tasks` | `project_id, status` | Composite | Filter tasks by status within a project |
| `tasks` | `created_at` | B-tree | Sort by creation date |
| `tasks` | `title, description` | GIN (tsvector) | Full-text search |
| `comments` | `task_id` | B-tree | Load comments for a task |
| `org_members` | `user_id, org_id` | Composite unique | Prevent duplicate membership |
| `notifications` | `user_id, is_read` | Composite | Unread notifications for a user |
| `audit_log` | `entity_id, entity_type` | Composite | History for a specific entity |
| `refresh_tokens` | `token_hash` | Unique B-tree | Token lookup |

---

## 7. Common Mistakes

### Not Indexing Foreign Keys

PostgreSQL does NOT automatically create indexes on foreign key columns (unlike MySQL). Always add them.

### Over-Indexing

Every index uses disk space and slows writes. Don't index every column; analyze your actual query patterns.

### Not Using EXPLAIN ANALYZE

Without `EXPLAIN ANALYZE`, you're guessing whether a query uses your index. Always verify.

### Wrong Column Order in Composite Indexes

The leftmost column must be used in the query for the index to be effective.

### Not Considering Index Maintenance

Indexes need `VACUUM` and `REINDEX` over time. Monitor index bloat.

---

## 8. Production Considerations

- **Monitor slow queries** — Use `pg_stat_statements` to find queries that need indexes
- **Create indexes concurrently** — `CREATE INDEX CONCURRENTLY` avoids locking the table
- **Monitor index usage** — Remove unused indexes with `pg_stat_user_indexes`
- **Index size** — Large indexes consume memory and slow down backups
- **Covering indexes** — Include all queried columns to avoid table lookups (index-only scans)

---

## 9. Prerequisites

- PostgreSQL basics (see `03-database/postgresql.md`)
- SQL query patterns (WHERE, JOIN, ORDER BY)
- Understanding of data structures (B-trees at a high level)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Identify columns that need indexes based on query patterns
- [ ] Choose the right index type for each use case
- [ ] Create composite and partial indexes
- [ ] Use `EXPLAIN ANALYZE` to verify index usage
- [ ] Define indexes in SQLAlchemy models and Alembic migrations
- [ ] Monitor and maintain indexes in production
