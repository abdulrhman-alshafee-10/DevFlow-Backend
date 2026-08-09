# Alembic — Database Migrations

## 1. What Is It?

Alembic is a database migration tool for SQLAlchemy. It tracks changes to your database schema over time and generates migration scripts that transform the database from one version to the next. Think of it as version control (like Git) for your database schema.

---

## 2. Why Does It Matter?

Without migrations:
- You'd need to manually ALTER tables when models change
- There's no record of what changed and when
- Multiple developers would overwrite each other's schema changes
- Rolling back a bad change is manual and error-prone
- Deploying schema changes to production is risky

With Alembic:
- Schema changes are tracked in version-controlled migration files
- Migrations can be applied in order (`upgrade`) or reversed (`downgrade`)
- Everyone works with the same schema
- Production deployments are predictable and repeatable

---

## 3. When Should I Use It?

- **Every time you change a model** — Add a column, rename a table, add an index
- **When you add new models** — New tables need migration scripts
- **When you change relationships** — Adding or removing foreign keys
- **When you need data migrations** — Transform existing data after schema changes
- **Before every deployment** — Run pending migrations as part of the deploy process

---

## 4. When Should I NOT Use It?

- **Initial database creation** — Use `alembic upgrade head` to create everything; don't manually create tables
- **Test databases** — Use `create_all()` for test databases that are recreated each test run (faster than running all migrations)
- **Throwaway experiments** — If you're just prototyping, you can defer migrations until the schema stabilizes

---

## 5. How Does It Work?

### Migration Lifecycle

```
1. Modify SQLAlchemy models
2. Run: alembic revision --autogenerate -m "add due_date to tasks"
3. Review the generated migration (auto-generation isn't perfect)
4. Run: alembic upgrade head (apply the migration)
```

### Migration File Structure

Each migration has:
- **Revision ID** — Unique identifier
- **Down revision** — Previous migration (forms a chain)
- **`upgrade()` function** — Applies the change
- **`downgrade()` function** — Reverses the change

### What Auto-Generation Detects

| Detects | Doesn't Detect |
|---|---|
| New tables | Table/column renames (looks like delete + create) |
| Removed tables | Data migrations |
| New columns | Custom CHECK constraints |
| Column type changes | Changes to Enum values |
| New indexes | Some complex default values |
| New foreign keys | |

### Always Review Auto-Generated Migrations

Auto-generation is a starting point, not a final product. Always review and test migrations before applying them to production.

---

## 6. How Does It Fit Into DevFlow?

DevFlow's migration history will grow as you build features:

```
001 - Initial migration (users table)
002 - Add organizations and org_members
003 - Add refresh_tokens table
004 - Add projects and project_members
005 - Add tasks table
006 - Add comments table
007 - Add attachments table
008 - Add notifications table
009 - Add audit_log table
010 - Add invitations table
011 - Add full-text search indexes
012 - Add task due_date and priority
...
```

Each project phase generates one or more migrations.

---

## 7. Common Mistakes

### Not Reviewing Auto-Generated Migrations

Blindly applying auto-generated migrations can drop columns, delete data, or create invalid schemas.

### Not Writing Downgrade Functions

If you can't downgrade, you can't roll back a bad deployment. Always implement `downgrade()`.

### Running Migrations on a Live Database Without Testing

Test migrations on a copy of the production database first.

### Creating Migration Conflicts

Two developers both create migration 005. Resolve by creating a merge migration.

### Not Handling Data Migrations

Adding a NOT NULL column to a table with existing data fails unless you provide a default or migrate data.

---

## 8. Production Considerations

- **Pre-deploy migrations** — Run migrations before deploying new code
- **Zero-downtime migrations** — Add new columns as nullable, deploy code, backfill data, then make non-null
- **Lock awareness** — Some ALTER TABLE operations lock the table. Use `CONCURRENTLY` for index creation
- **Backup before migration** — Always backup the database before applying migrations
- **Migration testing** — Run migrations against a copy of production data in CI/CD
- **Rollback plan** — Every migration should have a tested downgrade path

---

## 9. Prerequisites

- SQLAlchemy models (see `03-database/sqlalchemy.md`)
- PostgreSQL basics
- Command-line familiarity

---

## 10. What I Should Be Able to Do Afterward

- [ ] Initialize Alembic in a project
- [ ] Generate auto-generated migrations from model changes
- [ ] Review, edit, and customize migration scripts
- [ ] Apply and rollback migrations
- [ ] Handle data migrations alongside schema migrations
- [ ] Resolve migration conflicts
- [ ] Plan zero-downtime migrations for production
