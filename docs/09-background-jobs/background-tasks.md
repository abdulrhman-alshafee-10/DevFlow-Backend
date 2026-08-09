# Background Tasks and Jobs

## Background Tasks in FastAPI

FastAPI provides `BackgroundTasks` for simple async work that runs after a response is sent. Use it for lightweight operations that don't need reliability guarantees.

### When to Use BackgroundTasks
- Sending a single email notification
- Writing an audit log entry
- Updating a cache after a write

### When NOT to Use BackgroundTasks
- Long-running operations (>30 seconds)
- Operations that must not be lost (email campaigns)
- Operations that need retries on failure
- When the server could restart mid-task

---

## Task Queues (Celery / ARQ)

For reliable background processing, use a task queue. The queue decouples task submission from execution:

```
API Server                    Redis (Broker)              Worker Process
    │                              │                           │
    ├── enqueue task ────────────→ │                           │
    │   (return response)          ├── deliver task ─────────→ │
    │                              │                           ├── execute task
    │                              │   ←── report result ─────┤
```

### When to Use a Task Queue
- Sending emails (especially bulk)
- Processing file uploads (resizing, scanning)
- AI analysis (can take 10-60 seconds)
- Generating reports
- Syncing data with external services
- Any operation that needs retries

---

## DevFlow Background Jobs

| Job | Trigger | Queue | Priority |
|---|---|---|---|
| Send verification email | User registration | email | High |
| Send password reset email | Password reset request | email | High |
| Send invitation email | Team invitation | email | Medium |
| Send notification email | Task assignment, comment | email | Medium |
| Process file upload | Attachment upload | files | Medium |
| AI task analysis | User request | ai | Low |
| Generate project report | User request | reports | Low |
| Cleanup expired tokens | Scheduled (daily) | maintenance | Low |
| Sync search index | Data change | search | Medium |

---

## Retry Logic

Failed tasks should be retried with exponential backoff:

```
Attempt 1: immediate
Attempt 2: wait 10 seconds
Attempt 3: wait 30 seconds
Attempt 4: wait 60 seconds
Attempt 5: give up, log error, alert
```

### Idempotency

Retried tasks must be **idempotent** — running them twice should produce the same result as running them once. Example: sending an email twice is bad; checking "if email sent, skip" is idempotent.

---

## Scheduled Jobs

Recurring tasks that run on a schedule:

| Job | Schedule | Purpose |
|---|---|---|
| Clean expired tokens | Daily 2 AM | Remove expired refresh/reset tokens |
| Clean expired invitations | Daily 3 AM | Remove expired invitations |
| Generate daily digest | Daily 8 AM | Email summary of yesterday's activity |
| Health check external services | Every 5 min | Verify AI API, email service availability |

Use Celery Beat or APScheduler for scheduling.

---

## What I Should Be Able to Do Afterward

- [ ] Use FastAPI's BackgroundTasks for simple async work
- [ ] Set up a task queue with Celery or ARQ
- [ ] Define background tasks with retry logic
- [ ] Implement exponential backoff
- [ ] Make tasks idempotent
- [ ] Schedule recurring jobs
- [ ] Monitor background task failures
