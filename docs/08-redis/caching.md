# Caching with Redis

## 1. What Is It?

Caching stores the result of expensive operations (database queries, API calls, computations) in a fast-access store (Redis) so subsequent requests can be served without repeating the work. A well-designed caching strategy can reduce database load by 90%+ and dramatically improve response times.

---

## 2. Why Does It Matter?

Without caching, every request hits the database, even when the same data is requested repeatedly. This wastes database resources and increases response latency.

Example: DevFlow's permission check runs on every request. Without caching, every request makes 2-3 database queries just for authorization. With Redis caching, these queries happen once per minute.

---

## 5. How Does It Work?

### Cache-Aside Pattern (Lazy Loading)

```
1. Check Redis for cached data
2. If found (cache hit) → return cached data
3. If not found (cache miss) → query database
4. Store result in Redis with TTL
5. Return data
```

### Cache Invalidation Strategies

| Strategy | How | When to Use |
|---|---|---|
| **TTL-based** | Data expires after a set time | Good enough for most cases |
| **Write-through** | Update cache when data changes | When stale data is unacceptable |
| **Event-based** | Invalidate on specific events | Complex but precise |

### What to Cache in DevFlow

| Data | TTL | Invalidation |
|---|---|---|
| User profile | 5 min | On profile update |
| Organization membership/role | 5 min | On role change |
| Project settings | 10 min | On settings update |
| Task counts (dashboard) | 1 min | TTL-based |
| Permission lookups | 5 min | On role change |
| AI analysis results | 1 hour | TTL-based |

### What NOT to Cache

- **Frequently changing data** — Task lists that change every second
- **User-specific sensitive data** — Authentication tokens (use Redis directly, not as cache)
- **Large datasets** — Paginated lists (cache individual items instead)

---

## 7. Common Mistakes

### Not Invalidating on Writes

If you cache a user's profile but don't invalidate when they update it, they see stale data.

### Caching Too Aggressively

Caching everything adds complexity. Start with the slowest queries and highest-frequency reads.

### Cache Stampede

When a popular cache key expires, hundreds of requests simultaneously query the database. Use mutex locks or staggered TTLs.

### Not Handling Cache Failures

If Redis is down, fall back to database queries. Never let a cache failure crash the app.

---

## What I Should Be Able to Do Afterward

- [ ] Implement cache-aside pattern with Redis
- [ ] Choose appropriate TTLs for different data types
- [ ] Invalidate cache entries on data changes
- [ ] Handle cache stampedes
- [ ] Degrade gracefully when Redis is unavailable
