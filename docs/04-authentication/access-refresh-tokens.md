# Access & Refresh Tokens

## 1. What Is It?

A two-token authentication strategy where:
- **Access Token** — A short-lived JWT (15-30 min) used for API authentication
- **Refresh Token** — A long-lived token (7-30 days) used to obtain new access tokens without re-entering credentials

This pattern balances security (short-lived access) with user experience (long sessions without re-login).

---

## 2. Why Does It Matter?

Using only access tokens creates a tradeoff:
- **Short-lived** → Secure, but users must log in frequently (bad UX)
- **Long-lived** → Convenient, but a stolen token gives extended access (bad security)

The dual-token strategy solves both:
- Access tokens expire quickly, limiting damage from theft
- Refresh tokens provide long sessions without exposing credentials
- Refresh tokens can be revoked instantly (they're stored in the database)

---

## 3. When Should I Use It?

- **Every application with user sessions** — This is the standard approach
- **When you need revocable sessions** — Refresh tokens can be revoked
- **Multi-device support** — Each device has its own refresh token

---

## 4. When Should I NOT Use It?

- **Machine-to-machine APIs** — Use API keys or client credentials instead
- **Single-use tokens** — Email verification and password reset use single-use tokens, not refresh tokens

---

## 5. How Does It Work?

### Token Lifecycle

```
Login:
├── Verify credentials
├── Generate access token (JWT, 15 min)
├── Generate refresh token (opaque, 7 days)
├── Hash refresh token and store in DB
├── Return access token in response body
└── Set refresh token in HTTP-only secure cookie

API Request:
├── Client sends: Authorization: Bearer <access_token>
├── Server validates JWT signature and expiration
└── Request proceeds

Token Refresh (when access token expires):
├── Client sends refresh token (from cookie)
├── Server looks up hashed token in DB
├── Server verifies token is not revoked or expired
├── Server generates NEW access token
├── Server generates NEW refresh token (ROTATION)
├── Server revokes OLD refresh token
├── Return new tokens
└── If old token was already used → REVOKE ALL tokens (theft detected)

Logout:
├── Server revokes refresh token in DB
└── Client discards access token
```

### Refresh Token Rotation

Every time a refresh token is used, a new one is issued and the old one is invalidated. This provides:

1. **Theft detection** — If an attacker uses a stolen token, the legitimate user's next refresh fails (token already rotated). This signals a breach
2. **Limited window** — A stolen refresh token can only be used once
3. **Automatic cleanup** — Old tokens don't accumulate

### Token Storage

| Token | Client Storage | Server Storage |
|---|---|---|
| Access Token | JavaScript memory (NOT localStorage) | Not stored (stateless) |
| Refresh Token | HTTP-only, Secure, SameSite cookie | Hashed in database |

**Why not localStorage?** XSS attacks can read localStorage. HTTP-only cookies are inaccessible to JavaScript.

---

## 6. How Does It Fit Into DevFlow?

### Database: RefreshToken Table

```
RefreshToken:
  id: UUID (PK)
  user_id: UUID (FK → users)
  token_hash: str (hashed token)
  expires_at: datetime
  revoked_at: datetime | None
  replaced_by: UUID | None (points to the new token after rotation)
  device_info: str | None (browser, OS)
  ip_address: str | None
  created_at: datetime
```

### Endpoints

- `POST /auth/login` — Returns access token + sets refresh cookie
- `POST /auth/refresh` — Rotates refresh token, returns new access token
- `POST /auth/logout` — Revokes refresh token
- `POST /auth/logout-all` — Revokes ALL refresh tokens for the user (all devices)

### Password Change → Revoke All Tokens

When a user changes their password, all existing refresh tokens are revoked. This ensures:
- Stolen devices lose access
- Compromised sessions are terminated

---

## 7. Common Mistakes

### Not Rotating Refresh Tokens

Without rotation, a stolen refresh token provides indefinite access.

### Storing Access Tokens in localStorage

XSS attacks can steal tokens from localStorage. Use memory for access tokens and HTTP-only cookies for refresh tokens.

### Not Revoking Tokens on Password Change

If a user changes their password because their account was compromised, old tokens must be invalidated.

### Not Handling Token Reuse Detection

If a revoked refresh token is used, it means either the legitimate user or an attacker has the old token. Revoke all tokens for safety.

### Setting Refresh Tokens Too Long

30 days is reasonable. 1 year is too long — too much time for a stolen token to be exploited.

---

## 8. Production Considerations

- **Token family tracking** — Track which tokens replaced which for reuse detection
- **Device tracking** — Store device info with each refresh token so users can see active sessions
- **Geographic alerts** — Alert users when a refresh token is used from a new location
- **Cleanup job** — Periodically delete expired/revoked refresh tokens from the database
- **Rate limiting** — Limit refresh requests to prevent token harvesting

---

## 9. Prerequisites

- JWT (see `04-authentication/jwt.md`)
- Password hashing (see `04-authentication/password-hashing.md`)
- HTTP cookies
- Database operations

---

## 10. What I Should Be Able to Do Afterward

- [ ] Implement a dual access/refresh token system
- [ ] Implement refresh token rotation
- [ ] Detect refresh token reuse (theft detection)
- [ ] Store refresh tokens securely in the database
- [ ] Revoke tokens on logout and password change
- [ ] Set HTTP-only secure cookies for refresh tokens
- [ ] Explain the security tradeoffs of different token strategies
