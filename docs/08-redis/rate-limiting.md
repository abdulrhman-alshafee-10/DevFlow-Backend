# Rate Limiting

## 1. What Is It?

Rate limiting restricts the number of requests a client can make within a time window. It prevents abuse, protects resources, and ensures fair usage of the API.

---

## 2. Why Does It Matter?

Without rate limiting:
- A single user can overwhelm your server with requests
- Brute-force login attacks go unchecked
- API scraping depletes your resources
- AI endpoints (which cost money per call) have no cost controls
- DDoS attacks have maximum impact

---

## 5. How Does It Work?

### Algorithms

| Algorithm | How | Best For |
|---|---|---|
| **Fixed Window** | Count requests per time window (e.g., 100/min) | Simple, most common |
| **Sliding Window** | Smooths across window boundaries | More accurate |
| **Token Bucket** | Tokens regenerate over time; each request costs a token | Allowing bursts |
| **Leaky Bucket** | Requests processed at a fixed rate | Constant throughput |

### Redis Implementation (Fixed Window)

```
Key: rate_limit:{user_id}:{window}
Operation:
  1. INCR key
  2. If count == 1, SET EXPIRE key 60  (60-second window)
  3. If count > limit, reject with 429
```

### DevFlow Rate Limits

| Endpoint | Limit | Window | Key |
|---|---|---|---|
| `POST /auth/login` | 5 | 15 min | IP address |
| `POST /auth/register` | 3 | 1 hour | IP address |
| `POST /auth/forgot-password` | 3 | 1 hour | Email |
| `POST /auth/resend-verification` | 3 | 1 hour | Email |
| General API | 100 | 1 min | User ID |
| `POST /ai/*` | 20 | 1 hour | User ID |
| WebSocket connections | 5 | 1 min | User ID |

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312260
Retry-After: 30  (only on 429 responses)
```

---

## What I Should Be Able to Do Afterward

- [ ] Implement rate limiting with Redis
- [ ] Choose appropriate limits for different endpoints
- [ ] Return proper rate limit headers
- [ ] Handle rate limiting as middleware or dependency
- [ ] Distinguish between IP-based and user-based rate limiting
