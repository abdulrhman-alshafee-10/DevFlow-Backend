# Password Reset

## 1. What Is It?

Password reset is the process of allowing a user who has forgotten their password to set a new one. It involves sending a secure reset link to the user's verified email address, which they use to create a new password.

---

## 2. Why Does It Matter?

Users forget passwords. Without a secure reset mechanism, locked-out users can't access their accounts. A poorly implemented reset mechanism is one of the most common attack vectors — it can allow account takeover.

---

## 3. When Should I Use It?

- **Forgotten password** — User can't log in
- **Compromised account** — User wants to change password after a suspected breach
- **Admin-initiated reset** — Admin forces a password reset for a user

---

## 4. When Should I NOT Use It?

- **User knows their current password** — Use "change password" (requires current password verification)
- **OAuth-only accounts** — Users who signed up with Google don't have a DevFlow password

---

## 5. How Does It Work?

### Password Reset Flow

```
1. User clicks "Forgot Password"
2. User enters their email
3. Server generates a reset token (ALWAYS respond "if this email exists, we sent a link")
4. If email exists:
   a. Generate cryptographically random token
   b. Store token hash in Redis with 1-hour TTL
   c. Send email with reset link: https://devflow.com/reset-password?token=xyz
5. User clicks the link
6. User enters new password
7. Server validates:
   a. Token exists and is not expired
   b. Token has not been used
   c. New password meets requirements
8. Server:
   a. Hashes new password
   b. Updates user's password
   c. Invalidates the reset token
   d. Revokes ALL refresh tokens (end all sessions)
   e. Sends confirmation email
```

### Critical Security Requirement: Constant-Time Response

**NEVER** reveal whether an email exists in your system:

- ✅ "If this email is registered, we've sent a reset link"
- ❌ "No account found with that email" (reveals registered emails)

Process the request the same way regardless:
- Email exists → Send reset email, return success
- Email doesn't exist → Do nothing, return same success message

---

## 6. How Does It Fit Into DevFlow?

### Endpoints

- `POST /auth/forgot-password` — Request a password reset (accepts email)
- `POST /auth/reset-password` — Submit new password with reset token

### Security Measures

- Reset tokens expire in 1 hour
- Tokens are single-use (deleted after use)
- All existing sessions (refresh tokens) are revoked after reset
- Rate-limited to 3 requests per email per hour
- Token is hashed before storage (like passwords)

---

## 7. Common Mistakes

### Revealing Whether an Email Exists

This is the #1 mistake. It enables email enumeration attacks.

### Not Revoking Existing Sessions

If a user resets their password because their account was compromised, keeping old sessions active defeats the purpose.

### Predictable Reset Tokens

Use `secrets.token_urlsafe(32)`, not UUIDs or timestamps.

### No Token Expiration

Reset tokens without expiration are permanent backdoors.

### Allowing Password Reuse

The new password should not be the same as the current one.

---

## 8. Production Considerations

- **Email timing** — Process reset requests in a background task to prevent timing attacks
- **Logging** — Log password reset attempts (without the token)
- **Notification** — Email the user when their password is successfully reset
- **Brute-force protection** — Rate-limit both the request and the reset endpoints

---

## 9. Prerequisites

- Email verification (see `04-authentication/email-verification.md`)
- Password hashing (see `04-authentication/password-hashing.md`)
- Token generation

---

## 10. What I Should Be Able to Do Afterward

- [ ] Implement a secure password reset flow
- [ ] Prevent email enumeration
- [ ] Generate and validate single-use reset tokens
- [ ] Revoke all sessions after a password reset
- [ ] Rate-limit reset requests
