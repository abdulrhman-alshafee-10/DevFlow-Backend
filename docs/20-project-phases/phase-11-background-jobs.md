# Phase 11 — Background Jobs

## Objective

Set up a proper background job system with a task queue (Celery or ARQ), replacing simple FastAPI BackgroundTasks for operations that need reliability, retries, and monitoring.

---

## Concepts Learned

- Task queues vs. BackgroundTasks
- Worker processes
- Retry logic with exponential backoff
- Idempotent task design
- Scheduled/periodic jobs
- Job monitoring and error handling
- Dead letter queues

**Relevant docs**:
- `09-background-jobs/background-tasks.md`

---

## Features After This Phase

- [ ] Task queue set up with Celery or ARQ
- [ ] Email sending moved to background workers
- [ ] Notification emails sent asynchronously
- [ ] File processing in background workers
- [ ] Retry logic with exponential backoff
- [ ] Scheduled cleanup jobs (expired tokens, old notifications)
- [ ] Worker health monitoring

---

## Background Jobs to Implement

| Job | Trigger | Retry Policy | Idempotent? |
|---|---|---|---|
| Send email | Event (registration, reset, etc.) | 3 retries, exponential backoff | Yes (check if already sent) |
| Process file upload | File uploaded | 2 retries | Yes (check if already processed) |
| Clean expired tokens | Scheduled (daily 2 AM) | 1 retry | Yes |
| Clean old notifications | Scheduled (weekly) | 1 retry | Yes |
| Generate daily digest | Scheduled (daily 8 AM) | 1 retry | Yes (check if today's digest exists) |
| Sync search index | Event (task CRUD) | 3 retries | Yes |

---

## Completion Checklist

- [ ] Task queue infrastructure set up (Celery/ARQ + Redis as broker)
- [ ] Worker Dockerfile created
- [ ] Worker added to docker-compose.yml
- [ ] All email sending moved to background tasks
- [ ] Retry logic implemented with exponential backoff
- [ ] Scheduled cleanup jobs configured
- [ ] Worker health check endpoint
- [ ] Task failure logging and alerting
- [ ] All tasks are idempotent
- [ ] Tests for background task execution
