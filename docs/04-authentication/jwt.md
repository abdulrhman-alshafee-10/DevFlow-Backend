# JSON Web Tokens (JWT)

## 1. What Is It?

A JSON Web Token (JWT) is a compact, URL-safe token format that contains claims (pieces of information) about a user. It's cryptographically signed, so the server can verify its authenticity without storing it in a database. JWTs are the standard mechanism for stateless API authentication.

---

## 2. Why Does It Matter?

JWTs enable **stateless authentication** — the server doesn't need to store session data. The token itself contains everything needed to identify the user. This means:

- **Scalability** — Any server instance can validate the token (no shared session store)
- **Performance** — No database lookup needed for authentication
- **Flexibility** — Tokens can contain custom claims (roles, permissions)
- **Interoperability** — Standard format understood by all languages and frameworks

---

## 3. When Should I Use It?

- **API authentication** — The primary use case in DevFlow
- **Service-to-service communication** — Microservices can verify identity without a shared database
- **Short-lived authorization** — Access tokens that expire quickly

---

## 4. When Should I NOT Use It?

- **Session management** — JWTs are NOT sessions. You can't revoke a JWT before it expires (without a blacklist)
- **Storing sensitive data** — JWTs are encoded, not encrypted. Anyone can read the payload
- **Long-lived tokens** — Use opaque refresh tokens instead
- **When you need instant revocation** — A blacklist adds state, defeating the stateless advantage

---

## 5. How Does It Work?

### JWT Structure

A JWT has three parts separated by dots:

```
header.payload.signature

eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMTIzIn0.signature
```

**Header** (base64url encoded):
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload** (base64url encoded):
```json
{
  "sub": "user-uuid-123",      // Subject (user ID)
  "exp": 1705312200,            // Expiration time
  "iat": 1705310400,            // Issued at
  "type": "access"              // Custom claim
}
```

**Signature**:
```
HMAC-SHA256(base64url(header) + "." + base64url(payload), secret_key)
```

### Signing Algorithms

| Algorithm | Type | Use Case |
|---|---|---|
| HS256 | Symmetric (shared secret) | Simple; good for single-service apps |
| RS256 | Asymmetric (public/private key) | Better for microservices; anyone can verify with the public key |
| ES256 | Asymmetric (elliptic curve) | Smaller keys, similar security to RS256 |

**DevFlow recommendation**: Start with HS256 for simplicity. Upgrade to RS256 if you add microservices.

### Token Lifecycle

```
Login → Generate JWT (signed with secret) → Send to client
    ↓
Client sends JWT in Authorization: Bearer <token>
    ↓
Server validates signature → Checks expiration → Extracts user ID
    ↓
Request proceeds with authenticated user context
```

---

## 6. How Does It Fit Into DevFlow?

**Access Token Claims**:
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "type": "access",
  "exp": 1705312200,
  "iat": 1705310400
}
```

**Token Usage**:
- Access tokens are sent in the `Authorization: Bearer <token>` header
- The `get_current_user` dependency extracts and validates the JWT
- User ID from the `sub` claim is used to load the full user from the database
- Expired tokens return 401 with a clear error message

**What NOT to Put in the JWT**:
- Password hashes
- Email addresses (GDPR concerns)
- Roles/permissions (they can change; check the database)

---

## 7. Common Mistakes

### Putting Too Much Data in the JWT

JWTs are sent with every request. Large tokens waste bandwidth and headers have size limits.

### Not Validating Expiration

Always check the `exp` claim. An expired token is invalid, period.

### Using JWT for Sessions

JWTs can't be revoked before expiration. If you need immediate revocation, you need a token blacklist (which adds state).

### Exposing the Signing Secret

If the secret is compromised, anyone can forge tokens. Store it securely (environment variables, secrets manager).

### Not Using HTTPS

JWTs sent over HTTP can be intercepted and replayed. Always use HTTPS in production.

---

## 8. Production Considerations

- **Secret rotation** — Plan for rotating JWT signing keys (support multiple valid keys during transition)
- **Token blacklist** — For logout and security events, maintain a Redis-based blacklist of revoked tokens
- **Clock skew** — Allow a few seconds of tolerance for `exp` validation across servers
- **Token size** — Keep payloads small; measure header sizes
- **Algorithm confusion** — Explicitly specify the algorithm when verifying; never accept `none`

---

## 9. Prerequisites

- HTTP headers and the Authorization header
- JSON format
- Base64 encoding (at a high level)
- Symmetric vs. asymmetric cryptography (at a high level)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain the three parts of a JWT
- [ ] Create and validate JWTs with python-jose or PyJWT
- [ ] Choose appropriate token lifetimes
- [ ] Implement JWT validation as a FastAPI dependency
- [ ] Understand signing algorithms (HS256 vs. RS256)
- [ ] List what should and should not be stored in JWT claims
