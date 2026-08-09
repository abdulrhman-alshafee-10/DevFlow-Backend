# Authentication Overview

## 1. What Is It?

Authentication is the process of verifying **who a user is**. It answers the question: "Are you who you claim to be?" This is different from authorization, which determines what an authenticated user is allowed to do.

In DevFlow, authentication involves:
- **Registration** — Creating a new user account
- **Login** — Verifying credentials and issuing tokens
- **Token management** — Using JWTs for stateless authentication
- **Session management** — Refresh tokens, rotation, and revocation
- **Identity verification** — Email verification, password reset

---

## 2. Why Does It Matter?

Authentication is the foundation of every security decision in your application. If authentication is broken:
- Anyone can impersonate any user
- Private data is exposed
- Actions cannot be attributed to users
- Your entire authorization system is meaningless

Getting authentication right is critical. Getting it wrong is catastrophic.

---

## 3. When Should I Use It?

- **Every endpoint that accesses user-specific data**
- **Every endpoint that modifies data**
- **Every WebSocket connection**
- **Background jobs that act on behalf of users**

Only truly public endpoints (health check, API docs, public content) should skip authentication.

---

## 4. When Should I NOT Use It?

- **Health check endpoints** — Must be accessible by monitoring systems
- **Public API documentation** — Swagger UI in development
- **Registration and login endpoints** — These create the authentication (chicken-and-egg)
- **Password reset initiation** — User is, by definition, not authenticated

---

## 5. How Does It Work?

### Authentication Flow in DevFlow

```
Registration Flow:
1. User submits email + password
2. Server hashes password with bcrypt
3. Server creates user record
4. Server sends verification email
5. User clicks verification link
6. Server marks email as verified

Login Flow:
1. User submits email + password
2. Server verifies password against hash
3. Server generates access token (short-lived JWT)
4. Server generates refresh token (long-lived, stored in DB)
5. Tokens returned to client (access in body, refresh in secure cookie)

Authenticated Request:
1. Client sends access token in Authorization header
2. Server validates JWT signature and expiration
3. Server extracts user ID from token
4. Server loads user from database
5. Request proceeds with authenticated user context

Token Refresh:
1. Access token expires
2. Client sends refresh token
3. Server validates refresh token against DB
4. Server generates new access + refresh tokens (rotation)
5. Old refresh token is revoked

Logout:
1. Client sends refresh token
2. Server revokes refresh token in DB
3. Access token will expire naturally (short-lived)
```

### Token Strategy

| Token | Type | Lifetime | Storage | Purpose |
|---|---|---|---|---|
| Access Token | JWT | 15-30 minutes | Client memory | API authentication |
| Refresh Token | Opaque | 7-30 days | HTTP-only cookie + DB | Get new access tokens |

---

## 6. How Does It Fit Into DevFlow?

Authentication is implemented in Phase 3 and touches almost everything:

- **Registration** — `POST /auth/register`
- **Login** — `POST /auth/login`
- **Logout** — `POST /auth/logout`
- **Refresh** — `POST /auth/refresh`
- **Current User** — `GET /auth/me`
- **Email Verification** — `POST /auth/verify-email`
- **Password Reset** — `POST /auth/forgot-password`, `POST /auth/reset-password`
- **Password Change** — `POST /auth/change-password`

Every subsequent phase depends on authentication being solid.

---

## 7. Common Mistakes

### Storing Passwords in Plain Text

Always hash with bcrypt (or argon2). Never store, log, or expose plain-text passwords.

### Using Long-Lived Access Tokens

Access tokens should be short-lived (15-30 min). Use refresh tokens for long sessions.

### Not Implementing Refresh Token Rotation

Without rotation, a stolen refresh token gives permanent access. With rotation, each use generates a new token and invalidates the old one.

### Not Verifying Email Before Allowing Login

Users with unverified emails should have limited access. Require verification for sensitive operations.

### Exposing Tokens in URLs

Tokens in query parameters get logged in server logs, browser history, and referrer headers. Use headers and cookies.

---

## 8. Production Considerations

- **Rate limiting on login** — Prevent brute-force attacks
- **Account lockout** — Lock accounts after too many failed attempts
- **Token revocation on password change** — Invalidate all refresh tokens when the password changes
- **Secure cookie settings** — HttpOnly, Secure, SameSite=Lax/Strict
- **JWT secret rotation** — Plan for rotating signing keys without invalidating all tokens
- **Audit logging** — Log login attempts, failures, and password changes
- **Multi-device support** — Users may be logged in on multiple devices; each has its own refresh token

---

## 9. Prerequisites

- HTTP basics (headers, cookies, status codes)
- Hashing concepts (one-way functions)
- JSON and base64 encoding

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain the difference between authentication and authorization
- [ ] Describe the complete login/logout flow
- [ ] Understand access vs. refresh tokens
- [ ] Explain why refresh token rotation matters
- [ ] Design an authentication system for a multi-user application
- [ ] Identify common authentication vulnerabilities
