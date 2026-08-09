# Database Transactions

## 1. What Is It?

A transaction is a sequence of database operations that are treated as a single, atomic unit. Either all operations succeed and are committed, or all fail and are rolled back. Transactions ensure data consistency even when errors occur or multiple requests modify data simultaneously.

---

## 2. Why Does It Matter?

Without transactions, a multi-step operation can leave your database in an inconsistent state. For example, when a user creates a project in DevFlow:

1. Insert the project record
2. Add the creator as a project member with OWNER role
3. Create an audit log entry

If step 2 fails without a transaction, you'd have a project with no owner — an inconsistent state.

---

## 3. When Should I Use It?

- **Multi-table operations** — Creating an entity that spans multiple tables
- **Read-modify-write cycles** — Reading data, computing new values, writing back
- **Financial or critical data** — Any operation where partial completion is unacceptable
- **Batch operations** — Inserting or updating multiple related records

---

## 4. When Should I NOT Use It?

- **Read-only queries** — Implicit transactions are sufficient
- **Independent operations** — If two operations are truly independent, separate transactions improve throughput
- **Long-running operations** — Holding a transaction open for too long blocks other operations and risks deadlocks

---

## 5. How Does It Work?

### ACID Properties

| Property | Meaning | Example |
|---|---|---|
| **Atomicity** | All or nothing | Transfer money: debit AND credit, or neither |
| **Consistency** | Database moves from valid state to valid state | Foreign key constraints are never violated |
| **Isolation** | Concurrent transactions don't interfere | Two users updating the same task see consistent data |
| **Durability** | Committed data survives crashes | Once committed, the data is on disk |

### Isolation Levels

| Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Use Case |
|---|---|---|---|---|
| READ UNCOMMITTED | Yes | Yes | Yes | Never use |
| READ COMMITTED | No | Yes | Yes | PostgreSQL default; good for most cases |
| REPEATABLE READ | No | No | Yes | Financial calculations |
| SERIALIZABLE | No | No | No | Critical consistency; highest overhead |

### SQLAlchemy Transaction Patterns

The `AsyncSession` manages transactions. By default, a transaction starts with the first operation and must be explicitly committed.

Common patterns:
- **Auto-commit per request** — Commit at the end of the request if no errors
- **Explicit commits** — Commit at specific points in your service logic
- **Nested transactions (savepoints)** — Save intermediate state within a transaction

---

## 6. How Does It Fit Into DevFlow?

Transaction-critical operations in DevFlow:

- **User registration** — Create user + create default settings
- **Organization creation** — Create org + add creator as OWNER
- **Task creation** — Create task + create audit log + send notification
- **Task assignment** — Update task + create notification + create audit log
- **Invitation acceptance** — Create membership + update invitation status + create audit log
- **Project deletion** — Delete project + delete tasks + delete comments + delete attachments

The service layer is responsible for transaction boundaries. The repository performs individual operations; the service wraps them in a transaction.

---

## 7. Common Mistakes

### Committing Too Early

If you commit after each operation, you lose atomicity. Wait until all related operations succeed.

### Not Rolling Back on Errors

Exceptions should trigger rollback. With `async with` session patterns, this is handled automatically.

### Holding Transactions Open Too Long

Long transactions lock resources. Keep transactions as short as possible.

### Deadlocks

Two transactions updating the same rows in different orders can deadlock. Solution: always access tables in a consistent order, use row-level locks, and implement retry logic.

### N+1 Queries Inside a Transaction

Loading entities one by one in a loop inside a transaction is slow and holds locks longer.

---

## 8. Production Considerations

- **Deadlock detection** — Monitor and alert on deadlocks
- **Retry logic** — Implement automatic retries for transient failures (deadlocks, serialization failures)
- **Connection pool timeouts** — Don't let transactions hold connections indefinitely
- **Savepoints for partial rollback** — Roll back part of a transaction without aborting everything
- **Advisory locks** — Use PostgreSQL advisory locks for application-level locking

---

## 9. Prerequisites

- SQL basics
- SQLAlchemy session management
- Understanding of concurrent access

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain ACID properties
- [ ] Use SQLAlchemy's async session for transactions
- [ ] Implement commit/rollback patterns
- [ ] Choose appropriate isolation levels
- [ ] Handle deadlocks with retry logic
- [ ] Use savepoints for nested transactions
- [ ] Design service methods with proper transaction boundaries
