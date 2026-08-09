# Temporary Data in Redis

## 1. What Is It?

Redis is ideal for storing short-lived data that needs to expire automatically. Using Redis's built-in TTL (Time-To-Live), you can store tokens, codes, and counters that clean themselves up without cron jobs or manual deletion.

---

## DevFlow Temporary Data

| Data | TTL | Purpose |
|---|---|---|
| Email verification tokens | 24 hours | Verify user email ownership |
| Password reset tokens | 1 hour | Allow password reset |
| Login attempt counters | 15 minutes | Brute-force protection |
| Account lockout flags | 30 minutes | Lock account after too many failures |
| JWT blacklist entries | Until JWT expiry | Revoked access tokens |
| WebSocket session data | Connection lifetime | Track active connections |
| Rate limit counters | 1-60 minutes | API rate limiting |
| OTP codes | 5 minutes | Two-factor authentication |
| Invitation tokens | 7 days | Team invitations |

### Key Design Pattern

```
Key format:    {purpose}:{identifier}:{token_or_id}
Examples:
  verify_email:user:550e8400-e29b...   → token hash
  reset_password:token:abc123def...    → user ID
  login_attempts:ip:192.168.1.1       → attempt count
  jwt_blacklist:jti:xyz789            → "revoked"
```

---

## What I Should Be Able to Do Afterward

- [ ] Store and retrieve temporary data in Redis with TTL
- [ ] Design a key naming convention for different data types
- [ ] Implement token storage for verification and reset flows
- [ ] Use atomic operations for counters (INCR, DECR)
- [ ] Handle key expiration gracefully
