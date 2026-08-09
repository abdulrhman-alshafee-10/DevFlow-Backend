# Phase 8 — Notifications

## Objective

Build a notification system that alerts users about events relevant to them: task assignments, comments, mentions, invitation responses, and more. Notifications are stored in the database and delivered in real-time via WebSockets (Phase 9).

---

## Concepts Learned

- Event-driven architecture (triggering notifications from actions)
- Notification system design
- Polymorphic data (different notification types with different payloads)
- JSONB columns for flexible data
- Batch operations (mark all as read)
- Notification preferences

**Relevant docs**:
- `03-database/postgresql.md` (JSONB)

---

## Features After This Phase

- [ ] Notifications created on key events
- [ ] List notifications (paginated, filterable by read status)
- [ ] Mark notification as read
- [ ] Mark all notifications as read
- [ ] Unread notification count
- [ ] Delete notifications

---

## Database Changes

### Notification Model

```
Table: notifications
  id:              UUID (PK)
  user_id:         UUID (FK → users, NOT NULL) — recipient
  organization_id: UUID (FK → organizations, NOT NULL)
  type:            VARCHAR(50) (NOT NULL) — task_assigned, comment_added, etc.
  title:           VARCHAR(500) (NOT NULL)
  message:         TEXT
  data:            JSONB — { "task_id": "...", "project_id": "...", "actor_name": "..." }
  is_read:         BOOLEAN (default=false)
  read_at:         TIMESTAMP WITH TIME ZONE (nullable)
  created_at:      TIMESTAMP WITH TIME ZONE

Indexes:
  - INDEX on (user_id, is_read) — unread notifications for a user
  - INDEX on user_id
  - INDEX on created_at
```

### Notification Types

```
task_assigned        — "Alice assigned you to 'Fix login bug'"
task_status_changed  — "Bob moved 'Fix login bug' to In Progress"
comment_added        — "Carol commented on 'Fix login bug'"
comment_mention      — "Dave mentioned you in a comment"
invitation_received  — "You've been invited to join Acme Corp"
invitation_accepted  — "Eve accepted your invitation"
member_role_changed  — "Your role in Acme Corp changed to Admin"
project_archived     — "Project 'Mobile App' was archived"
```

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/notifications` | List my notifications (paginated) | Yes |
| GET | `/api/v1/notifications/unread-count` | Get unread count | Yes |
| PATCH | `/api/v1/notifications/{id}/read` | Mark as read | Yes |
| POST | `/api/v1/notifications/read-all` | Mark all as read | Yes |
| DELETE | `/api/v1/notifications/{id}` | Delete notification | Yes |

---

## Testing Requirements

- Task assignment creates notification for assignee
- Comment creates notification for task assignee/creator
- Notification list returns only current user's notifications
- Mark as read updates is_read and read_at
- Mark all as read works correctly
- Unread count is accurate
- Cross-user notification access denied

---

## Completion Checklist

- [ ] Created Notification model
- [ ] Generated and applied migration
- [ ] Created notification repository and service
- [ ] Created notification endpoints
- [ ] Integrated notification creation into task service (task assigned, status changed)
- [ ] Integrated notification creation into comment service
- [ ] Integrated notification creation into invitation service
- [ ] Unread count endpoint works
- [ ] Batch mark-as-read works
- [ ] All authorization tests pass
