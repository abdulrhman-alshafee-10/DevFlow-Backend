# Email Verification

## 1. What Is It?

Email verification is the process of confirming that a user actually owns the email address they registered with. After registration, a verification link is sent to the user's email. Clicking the link proves they have access to that email address.

---

## 2. Why Does It Matter?

- **Prevents fake accounts** — Users can't register with someone else's email
- **Enables email communication** — Password reset and notifications require a valid email
- **Reduces spam** — Bots can't create usable accounts without email access
- **Legal compliance** — Some regulations require verified email addresses

---

## 3. When Should I Use It?

- **User registration** — Always verify email before granting full access
- **Email change** — Verify the new email before updating the account
- **Re-verification** — After a security incident, re-verify all accounts

---

## 4. When Should I NOT Use It?

- **OAuth/social login** — The identity provider has already verified the email
- **Internal/dev environments** — Skip verification in development for speed (but keep the code path)

---

## 5. How Does It Work?

### Verification Flow

```
1. User registers with email + password
2. Server creates user with is_email_verified = false
3. Server generates a verification token (random string or signed JWT)
4. Server stores token hash in Redis/DB with TTL (e.g., 24 hours)
5. Server sends email with verification link:
   https://devflow.com/verify-email?token=abc123
6. User clicks the link
7. Server validates the token (exists, not expired, not used)
8. Server sets is_email_verified = true
9. Server deletes/invalidates the token
```

### Token Strategies

| Strategy | Pros | Cons |
|---|---|---|
| Random token in Redis | Simple, auto-expires with TTL | Requires Redis |
| Signed JWT | No storage needed | Can't revoke before expiry |
| Random token in DB | Works without Redis | Need cleanup job for expired tokens |

**DevFlow recommendation**: Use Redis with a random token. The TTL handles expiration automatically.

---

## 6. How Does It Fit Into DevFlow?

- **Registration** → Send verification email → User verifies → Full access granted
- **Unverified users** can log in but have limited access (can't create organizations, projects, or tasks)
- **Resend verification** — `POST /auth/resend-verification` with rate limiting
- **Token expiration** — 24 hours; after that, request a new one

---

## 7. Common Mistakes

### Using Predictable Tokens

Tokens must be cryptographically random (use `secrets.token_urlsafe(32)`). Sequential or guessable tokens allow account takeover.

### Not Expiring Tokens

Verification tokens should expire (24 hours is standard). Indefinite tokens are a security risk.

### Not Rate-Limiting Resend

Without rate limiting, an attacker can trigger thousands of verification emails (email bombing).

### Allowing Full Access Without Verification

Unverified users should have restricted access until they verify their email.

---

## 8. Production Considerations

- **Email delivery** — Use a reliable email service (SendGrid, SES) to ensure delivery
- **Spam filters** — Configure SPF, DKIM, and DMARC to avoid spam folders
- **Token security** — Store hashed tokens, not plain text
- **Rate limiting** — Max 3 resends per hour per email
- **User experience** — Show a clear "check your email" message with resend option

---

## 9. Prerequisites

- Email sending (see `12-email/email-system.md`)
- Token generation (cryptographic randomness)
- Redis basics (see `08-redis/redis-basics.md`)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Implement a complete email verification flow
- [ ] Generate and validate secure verification tokens
- [ ] Store tokens with expiration
- [ ] Rate-limit verification email resending
- [ ] Restrict unverified users appropriately
