# Database Relationships

## 1. What Is It?

Database relationships define how tables are connected to each other. In a relational database, relationships are implemented through foreign keys — columns that reference the primary key of another table. SQLAlchemy's `relationship()` function creates Python-level attributes that let you navigate between related objects.

---

## 2. Why Does It Matter?

DevFlow's data is deeply interconnected. A task belongs to a project, which belongs to an organization, which has members who are users. Without properly modeled relationships:

- You'd need manual joins for every query
- Data integrity would depend on application code, not the database
- Cascading operations (delete a project → delete its tasks) would be manual
- Navigation between objects would require explicit queries

---

## 3. When Should I Use It?

- **One-to-many** — Organization has many projects, project has many tasks
- **Many-to-many** — Users belong to many organizations (through membership table)
- **One-to-one** — User has one profile (less common)
- **Self-referential** — Task has a parent task (subtasks)
- **Polymorphic** — Different notification types stored in one table

---

## 4. When Should I NOT Use It?

- **Loose coupling** — If two entities are only weakly related, a foreign key might be too tight
- **Cross-database references** — Foreign keys don't work across databases
- **High-write scenarios** — Foreign key checks add overhead to inserts; consider deferring checks
- **Event sourcing** — When you store events instead of state, relationships work differently

---

## 5. How Does It Work?

### Relationship Types in DevFlow

**One-to-Many**: Organization → Projects
```
organizations table: id (PK)
projects table: id (PK), organization_id (FK → organizations.id)
```

**Many-to-Many via Association Table**: Users ↔ Organizations
```
users table: id (PK)
organizations table: id (PK)
organization_members table: user_id (FK), organization_id (FK), role
```

**Self-Referential**: Task → Subtasks
```
tasks table: id (PK), parent_task_id (FK → tasks.id, nullable)
```

### Cascade Behavior

| Cascade | Meaning |
|---|---|
| `cascade="save-update"` | When parent is saved, save children too |
| `cascade="delete"` | When parent is deleted, delete children |
| `cascade="all, delete-orphan"` | Full lifecycle management |
| `ondelete="CASCADE"` | Database-level cascade (safer) |
| `ondelete="SET NULL"` | Set FK to NULL on parent deletion |
| `ondelete="RESTRICT"` | Prevent parent deletion if children exist |

### DevFlow Entity Relationship Map

```
User (1) ──── (M) OrganizationMember (M) ──── (1) Organization
User (1) ──── (M) ProjectMember (M) ──── (1) Project
User (1) ──── (M) Task (as creator)
User (1) ──── (M) Task (as assignee)
User (1) ──── (M) Comment
User (1) ──── (M) RefreshToken
User (1) ──── (M) Notification

Organization (1) ──── (M) Project
Organization (1) ──── (M) Invitation

Project (1) ──── (M) Task

Task (1) ──── (M) Comment
Task (1) ──── (M) Attachment
Task (1) ──── (M) Task (subtasks, self-referential)
Task (1) ──── (M) AuditLog
```

---

## 6. How Does It Fit Into DevFlow?

Every query in DevFlow traverses relationships:

- **"Show me all tasks in my project"** — Task → Project → ProjectMember → User
- **"Show me all organizations I belong to"** — User → OrganizationMember → Organization
- **"Show me a task with its comments"** — Task → Comments (with User eager-loaded)
- **"Delete a project"** — Cascade to tasks, comments, attachments
- **"Show me who assigned this task"** — Task → User (creator)

---

## 7. Common Mistakes

### Not Using Database-Level Foreign Keys

SQLAlchemy relationships without actual foreign key constraints mean the database won't prevent orphaned records.

### Eager Loading Everything

Loading all relationships for every query wastes memory and time. Load only what you need.

### Bidirectional Relationships Without `back_populates`

If both sides of a relationship don't reference each other, SQLAlchemy can't keep them in sync within a session.

### Cascade Confusion

ORM-level cascades and database-level cascades are different. Use database-level `ondelete` for safety; ORM cascades for convenience.

### Not Handling Circular References in Serialization

User → Tasks → User (assignee) creates infinite recursion when serializing to JSON. Pydantic response models must break this cycle.

---

## 8. Production Considerations

- **Index foreign keys** — PostgreSQL doesn't automatically index foreign key columns; add indexes for columns used in joins
- **Cascade carefully** — Deleting an organization shouldn't accidentally delete all user accounts
- **Soft deletes** — Consider `deleted_at` timestamps instead of hard deletes for audit trails
- **Data migration** — Adding or changing relationships requires careful Alembic migrations

---

## 9. Prerequisites

- SQL joins and foreign keys
- SQLAlchemy models (see `03-database/sqlalchemy.md`)
- Python type hints

---

## 10. What I Should Be Able to Do Afterward

- [ ] Define one-to-many, many-to-many, and self-referential relationships
- [ ] Use association tables for many-to-many with extra data
- [ ] Configure cascade behavior (ORM and database level)
- [ ] Choose appropriate relationship loading strategies
- [ ] Navigate relationships in queries
- [ ] Avoid circular reference issues in serialization
