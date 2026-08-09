# Phase 3 — Authentication

## Objective

Implement a complete authentication system: registration, login, logout, JWT access/refresh tokens with rotation, email verification, password reset, and password change. After this phase, all user-facing endpoints require authentication.

---

## Concepts Learned

- Password hashing with bcrypt
- JWT creation and validation
- Access token and refresh token strategy
- Refresh token rotation with reuse detection
- OAuth2PasswordBearer in FastAPI
- Dependency injection for current user extraction
- Secure cookies (HttpOnly, Secure, SameSite)
- Email verification flow
- Password reset flow
- Rate limiting on auth endpoints
- Token revocation

**Relevant docs**:
- `04-authentication/` (all files)
- `08-redis/redis-basics.md` (for token storage)
- `08-redis/rate-limiting.md`

---

## Features After This Phase

- [ ] User registration with password hashing
- [ ] Login returns access token (body) + refresh token (cookie)
- [ ] All protected endpoints require valid access token
- [ ] Token refresh with rotation (new refresh token each time)
- [ ] Refresh token reuse detection (revoke all tokens if detected)
- [ ] Logout revokes refresh token
- [ ] Logout from all devices revokes all refresh tokens
- [ ] Email verification flow (send + verify)
- [ ] Password reset flow (request + reset)
- [ ] Password change (requires current password)
- [ ] Current user endpoint (`GET /auth/me`)
- [ ] Rate limiting on login, register, and password reset
- [ ] Brute-force protection (account lockout after N failed attempts)

---

## Database Changes

### RefreshToken Model

```
Table: refresh_tokens
  id:           UUID (PK)
  user_id:      UUID (FK → users, NOT NULL)
  token_hash:   VARCHAR(255) (UNIQUE, NOT NULL)
  expires_at:   TIMESTAMP WITH TIME ZONE (NOT NULL)
  revoked_at:   TIMESTAMP WITH TIME ZONE (nullable)
  replaced_by:  UUID (FK → refresh_tokens, nullable)
  device_info:  VARCHAR(500) (nullable)
  ip_address:   VARCHAR(45) (nullable)
  created_at:   TIMESTAMP WITH TIME ZONE

Indexes:
  - UNIQUE on token_hash
  - INDEX on user_id
  - INDEX on expires_at (for cleanup queries)
```

### Redis Keys

```
verify_email:{token}          → user_id (TTL: 24h)
reset_password:{token}        → user_id (TTL: 1h)
login_attempts:ip:{ip}        → count (TTL: 15min)
login_attempts:email:{email}  → count (TTL: 15min)
account_lockout:{user_id}     → "locked" (TTL: 30min)
jwt_blacklist:jti:{jti}       → "revoked" (TTL: access token lifetime)
```

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login with email + password | No |
| POST | `/api/v1/auth/logout` | Logout (revoke refresh token) | Yes |
| POST | `/api/v1/auth/logout-all` | Logout all devices | Yes |
| POST | `/api/v1/auth/refresh` | Refresh access token | Cookie |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| POST | `/api/v1/auth/verify-email` | Verify email with token | No |
| POST | `/api/v1/auth/resend-verification` | Resend verification email | Yes |
| POST | `/api/v1/auth/forgot-password` | Request password reset | No |
| POST | `/api/v1/auth/reset-password` | Reset password with token | No |
| POST | `/api/v1/auth/change-password` | Change password (old + new) | Yes |

### Request/Response Details

**POST /auth/register**
```
Request:  { email, username, password, full_name }
Response: { id, email, username, full_name, is_email_verified: false }
Status:   201 Created
Errors:   409 (email/username exists), 422 (validation error)
Side effects: Send verification email
```

**POST /auth/login**
```
Request:  { email, password }
Response: { access_token, token_type: "bearer", user: {...} }
Cookie:   Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth
Status:   200 OK
Errors:   401 (invalid credentials), 423 (account locked)
```

**POST /auth/refresh**
```
Request:  (refresh token from cookie)
Response: { access_token, token_type: "bearer" }
Cookie:   Updated refresh_token (rotation)
Status:   200 OK
Errors:   401 (invalid/expired/revoked token)
```

**POST /auth/forgot-password**
```
Request:  { email }
Response: { message: "If this email is registered, we've sent a reset link" }
Status:   200 OK (ALWAYS, even if email doesn't exist)
```

---

## Authentication/Authorization Requirements

- `register`, `login`, `forgot-password`, `reset-password`, `verify-email` → public
- `me`, `logout`, `logout-all`, `change-password`, `resend-verification` → requires valid access token
- `refresh` → requires valid refresh token (from cookie)
- All previously public user endpoints → now require authentication

---

## Testing Requirements

### Registration Tests
- Register with valid data → 201
- Register with existing email → 409
- Register with existing username → 409
- Register with weak password → 422
- Register with invalid email → 422
- Verification email is triggered

### Login Tests
- Login with valid credentials → 200 + tokens
- Login with wrong password → 401
- Login with non-existent email → 401 (same error, no enumeration)
- Response includes access token in body
- Response sets refresh token in HttpOnly cookie
- Rate limiting after 5 failed attempts → 429
- Account lockout after 10 failed attempts → 423

### Token Tests
- Access token expires after configured lifetime
- Expired access token → 401
- Tampered access token → 401
- Refresh with valid token → new access token + new refresh token
- Refresh with expired token → 401
- Refresh with revoked token → 401 + revoke all tokens (reuse detection)
- Old refresh token doesn't work after rotation

### Logout Tests
- Logout revokes refresh token
- Logout-all revokes all user's refresh tokens
- Refreshing after logout → 401

### Email Verification Tests
- Valid verification token → email marked as verified
- Expired token → 400
- Already-used token → 400
- Resend verification → new token sent, old token invalid

### Password Reset Tests
- Request for existing email → sends email
- Request for non-existent email → same response (no enumeration)
- Valid reset token → password updated
- All refresh tokens revoked after reset
- Expired token → 400
- Used token → 400

### Password Change Tests
- Correct current password + valid new password → 200
- Incorrect current password → 401
- All refresh tokens revoked after change

---

## Completion Checklist

- [ ] Redis running and connected (Docker)
- [ ] Created `app/utils/security.py` (password hashing, JWT functions)
- [ ] Created `app/models/refresh_token.py`
- [ ] Generated and applied RefreshToken migration
- [ ] Created `app/schemas/auth.py` (LoginRequest, RegisterRequest, TokenResponse, etc.)
- [ ] Created `app/repositories/refresh_token.py`
- [ ] Created `app/services/auth.py` with all auth logic
- [ ] Created `app/api/v1/auth.py` with all auth endpoints
- [ ] Created `app/api/deps.py` with `get_current_user` dependency
- [ ] Implemented refresh token rotation with reuse detection
- [ ] Implemented rate limiting on auth endpoints (Redis)
- [ ] Implemented brute-force protection with account lockout
- [ ] Implemented email verification flow (tokens in Redis)
- [ ] Implemented password reset flow (tokens in Redis)
- [ ] Protected all user endpoints with `get_current_user`
- [ ] All auth tests pass
- [ ] Verified refresh token is HttpOnly, Secure, SameSite cookie
- [ ] Verified password hash never appears in API responses
- [ ] Verified constant-time response for forgot-password (no email enumeration)
