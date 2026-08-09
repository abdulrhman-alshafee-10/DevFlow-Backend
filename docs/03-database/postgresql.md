# PostgreSQL

## 1. What Is It?

PostgreSQL (often called "Postgres") is an open-source, enterprise-grade relational database management system. It stores data in tables with rows and columns, enforces relationships between data, and provides a powerful query language (SQL) for reading and writing data.

---

## 2. Why Does It Matter?

PostgreSQL is the most popular database for production Python applications because:

- **ACID compliance** — Guarantees data integrity (Atomicity, Consistency, Isolation, Durability)
- **Rich feature set** — JSON/JSONB columns, full-text search, window functions, CTEs, array types
- **Extensibility** — Extensions like `pgvector` (for AI embeddings), `pg_trgm` (for fuzzy search)
- **Performance** — Advanced query planner, parallel queries, efficient indexing
- **Reliability** — Battle-tested in millions of production deployments
- **Ecosystem** — Excellent tooling, monitoring, and replication support

---

## 3. When Should I Use It?

- **Structured data with relationships** — Users, organizations, projects, tasks
- **Data integrity is critical** — Financial data, user accounts, permissions
- **Complex queries** — Joins, aggregations, subqueries
- **Full-text search** — Before you need Elasticsearch
- **JSONB data** — Semi-structured data alongside relational data
- **Multi-tenant applications** — Row-level security, schema separation

---

## 4. When Should I NOT Use It?

- **Simple key-value storage** — Redis is faster and simpler
- **Document-heavy workloads** — MongoDB might be more natural (though PostgreSQL's JSONB is very capable)
- **Time-series data at massive scale** — TimescaleDB (PostgreSQL extension) or InfluxDB
- **Graph-heavy queries** — Neo4j for graph-first workloads (though PostgreSQL's recursive CTEs handle many graph queries)

---

## 5. How Does It Work?

### Core Concepts

- **Database** — A collection of schemas
- **Schema** — A namespace for tables (default is `public`)
- **Table** — A collection of rows with defined columns
- **Row** — A single record
- **Column** — A field with a specific data type
- **Index** — A data structure that speeds up queries on specific columns
- **Constraint** — A rule enforced by the database (unique, not null, foreign key, check)
- **Transaction** — A group of operations that either all succeed or all fail

### Important PostgreSQL Types for DevFlow

| Type | Use Case |
|---|---|
| `UUID` | Primary keys (globally unique) |
| `VARCHAR(n)` | Short strings (names, emails) |
| `TEXT` | Long strings (descriptions, comments) |
| `BOOLEAN` | Flags (is_active, is_verified) |
| `TIMESTAMP WITH TIME ZONE` | Dates and times |
| `JSONB` | Semi-structured data (settings, metadata) |
| `INTEGER` | Counts, positions |
| `ENUM` | Fixed sets of values (status, priority) |
| `ARRAY` | Lists of values (tags) |

---

## 6. How Does It Fit Into DevFlow?

PostgreSQL is DevFlow's primary data store for:

- **Users** — Registration, profiles, authentication data
- **Organizations** — Multi-tenant workspaces
- **Projects** — Project metadata and settings
- **Tasks** — The core work items with status, priority, assignments
- **Comments** — Threaded discussions on tasks
- **Attachments** — Metadata about uploaded files
- **Notifications** — Stored notification records
- **Audit logs** — Who did what and when
- **Refresh tokens** — For authentication
- **Invitations** — Team invitations

Later, PostgreSQL's full-text search will be used for task and project search before considering Elasticsearch.

---

## 7. Common Mistakes

### Not Using UUIDs for Public IDs

Sequential integer IDs (1, 2, 3) are predictable and leak information (how many users exist). Use UUIDs for any ID exposed in the API.

### Not Setting Up Connection Pooling

Opening a new connection per request is slow. Use connection pooling (SQLAlchemy handles this with `create_async_engine`).

### Ignoring Indexes

Without indexes, queries on large tables do full table scans. Add indexes for columns used in WHERE, JOIN, and ORDER BY clauses.

### Not Using Transactions Properly

Multiple related operations should be in a single transaction. If one fails, all should roll back.

### Storing Files in the Database

Store file metadata in PostgreSQL, but store the actual file in object storage (S3/MinIO).

---

## 8. Production Considerations

- **Connection pooling** — Use PgBouncer or SQLAlchemy's built-in pooling
- **Backups** — Automated backups with point-in-time recovery
- **Replication** — Read replicas for read-heavy workloads
- **Monitoring** — Track slow queries, connection count, disk usage
- **Vacuuming** — PostgreSQL needs periodic cleanup (autovacuum handles this)
- **Migrations** — Use Alembic for schema changes; never modify production schemas manually
- **Security** — Use least-privilege database users; encrypt connections with SSL

---

## 9. Prerequisites

- Basic SQL (SELECT, INSERT, UPDATE, DELETE, JOIN)
- Understanding of relational database concepts (tables, rows, columns, keys)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Set up a PostgreSQL database for development
- [ ] Understand PostgreSQL data types and when to use each
- [ ] Create tables with appropriate constraints
- [ ] Write queries with joins, filters, and aggregations
- [ ] Understand indexes and when to add them
- [ ] Use UUIDs as primary keys
- [ ] Configure connection pooling
