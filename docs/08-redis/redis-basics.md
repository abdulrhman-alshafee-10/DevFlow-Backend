# Redis Basics

## 1. What Is It?

Redis is an in-memory data store that functions as a database, cache, message broker, and queue. It stores data in memory (RAM) rather than on disk, making it extremely fast — typically sub-millisecond response times. Redis supports multiple data structures: strings, hashes, lists, sets, sorted sets, and streams.

---

## 2. Why Does It Matter?

PostgreSQL is great for persistent, relational data, but it's not the right tool for everything. Redis fills the gaps:

- **Caching** — Store frequently accessed data in memory (100x faster than a database query)
- **Rate limiting** — Count requests per user/IP with atomic operations and auto-expiration
- **Temporary data** — Verification tokens, password reset tokens, OTPs with automatic TTL
- **Real-time features** — Pub/Sub for broadcasting events to WebSocket connections
- **Session data** — Store active sessions, token blacklists
- **Queues** — Message broker for background job queues (Celery/ARQ)

---

## 3. When Should I Use It?

- **When you need speed** — Caching hot data (user profiles, permission lookups)
- **When data is temporary** — Tokens, OTPs, rate limit counters (TTL handles cleanup)
- **When you need atomic counters** — Rate limiting, view counts
- **When you need pub/sub** — Broadcasting events to multiple subscribers
- **When you need a message broker** — Background job queues

---

## 4. When Should I NOT Use It?

- **As a primary database** — Redis is in-memory; data can be lost on restart (use persistence modes for critical data)
- **For complex queries** — No JOINs, no SQL, no relational queries
- **For large datasets** — Everything lives in RAM; storing 100GB in Redis is expensive
- **When durability is critical** — Use PostgreSQL for data that must survive crashes

---

## 5. How Does It Work?

### Key Data Structures

| Structure | Use Case | Example |
|---|---|---|
| **String** | Simple values, counters | `SET user:123:name "Alice"`, `INCR rate:ip:1.2.3.4` |
| **Hash** | Object-like data | `HSET user:123 name "Alice" role "admin"` |
| **List** | Queues, recent items | `LPUSH notifications:user:123 "new_task"` |
| **Set** | Unique collections | `SADD online_users user:123` |
| **Sorted Set** | Ranked data, leaderboards | `ZADD task_priorities 3 task:456` |
| **Stream** | Event log, message queue | `XADD events * type "task_created"` |

### TTL (Time-To-Live)

Every key can have an expiration time. When the TTL expires, Redis automatically deletes the key:

```
SET verification:token:abc123 user_id_456 EX 86400   # Expires in 24 hours
SET rate_limit:ip:1.2.3.4 1 EX 60                    # Expires in 60 seconds
```

### Pub/Sub

Redis Pub/Sub lets you broadcast messages to multiple subscribers:

```
Publisher:   PUBLISH task_updates '{"task_id": "123", "status": "done"}'
Subscriber:  SUBSCRIBE task_updates  → receives the message
```

---

## 6. How Does It Fit Into DevFlow?

| Feature | Redis Usage |
|---|---|
| **Caching** | Cache user profiles, permission lookups, project settings |
| **Rate limiting** | Track request counts per user/IP with TTL |
| **Email verification** | Store verification tokens with 24h TTL |
| **Password reset** | Store reset tokens with 1h TTL |
| **Token blacklist** | Store revoked JWT IDs until their natural expiration |
| **Real-time** | Pub/Sub for broadcasting task updates to WebSocket clients |
| **Background jobs** | Message broker for Celery/ARQ task queues |
| **Online presence** | Track which users are currently online |

---

## 7. Common Mistakes

### Not Setting TTL on Temporary Data

Without TTL, temporary data accumulates forever. Always set expiration on tokens, rate limit counters, and cache entries.

### Using Redis as a Primary Database

Redis should complement PostgreSQL, not replace it. Critical data belongs in PostgreSQL.

### Not Handling Redis Unavailability

If Redis goes down, your app shouldn't crash. Degrade gracefully (skip cache, allow requests through rate limiter).

### Key Naming Without Convention

Use a consistent naming convention: `resource:id:field` (e.g., `user:123:profile`, `rate:ip:1.2.3.4`).

---

## 8. Production Considerations

- **Persistence** — Configure RDB snapshots or AOF logging for data you can't afford to lose
- **Memory limits** — Set `maxmemory` and a eviction policy (`allkeys-lru` for caches)
- **Connection pooling** — Use a connection pool (aioredis handles this)
- **Monitoring** — Track memory usage, hit rates, and command latency
- **Sentinel/Cluster** — For high availability and horizontal scaling
- **Security** — Set a password, bind to internal interfaces, use TLS

---

## 9. Prerequisites

- Basic understanding of key-value stores
- Async/await (for aioredis/redis-py async)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Connect to Redis from FastAPI with async client
- [ ] Use strings, hashes, and sorted sets
- [ ] Set TTL on keys
- [ ] Implement basic caching with Redis
- [ ] Use Pub/Sub for event broadcasting
- [ ] Design a key naming convention
- [ ] Handle Redis unavailability gracefully
