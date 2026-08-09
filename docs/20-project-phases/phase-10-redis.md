# Phase 10 — Redis Integration

## Objective

Fully integrate Redis for caching, rate limiting, and temporary data management. While Redis was introduced in Phase 3 for token storage, this phase makes it a first-class component with caching strategies and comprehensive rate limiting.

---

## Concepts Learned

- Cache-aside pattern
- Cache invalidation strategies
- Rate limiting algorithms
- Redis as a session/temporary data store
- Graceful degradation when Redis is unavailable
- Key naming conventions
- TTL management

**Relevant docs**:
- `08-redis/` (all files)

---

## Features After This Phase

- [ ] Cache user profiles and permission lookups
- [ ] Cache project settings and member lists
- [ ] Rate limiting on all API endpoints
- [ ] Stricter rate limits on auth and AI endpoints
- [ ] Rate limit headers in responses
- [ ] Cache invalidation on data changes
- [ ] Graceful degradation when Redis is down

---

## Implementation

### Caching Targets

| Data | TTL | Invalidation Trigger |
|---|---|---|
| User profile | 5 min | Profile update |
| Org membership + role | 5 min | Role change, member add/remove |
| Project member list | 5 min | Member change |
| Task counts per project | 1 min | Task create/update/delete |
| Unread notification count | 30 sec | Notification create/read |

### Rate Limit Tiers

| Tier | Limit | Window | Applies To |
|---|---|---|---|
| General API | 100 req | 1 min | Authenticated user |
| Auth endpoints | 5 req | 15 min | IP address |
| Registration | 3 req | 1 hour | IP address |
| AI endpoints | 20 req | 1 hour | Authenticated user |
| File upload | 10 req | 1 min | Authenticated user |
| Search | 30 req | 1 min | Authenticated user |

---

## Completion Checklist

- [ ] Implemented cache-aside pattern as a reusable utility
- [ ] Added caching to user profile, permissions, and project settings
- [ ] Implemented cache invalidation in relevant services
- [ ] Comprehensive rate limiting across all endpoints
- [ ] Rate limit headers (`X-RateLimit-*`) in responses
- [ ] Graceful degradation tested (Redis down → app still works)
- [ ] Cache hit/miss logging for monitoring
- [ ] All existing tests still pass
