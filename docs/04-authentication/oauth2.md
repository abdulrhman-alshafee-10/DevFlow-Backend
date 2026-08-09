# OAuth2

## 1. What Is It?

OAuth 2.0 is an authorization framework that allows third-party applications to access a user's resources without exposing their credentials. It's the protocol behind "Login with Google/GitHub/Facebook" buttons and API access delegation.

---

## 2. Why Does It Matter?

OAuth2 is the industry standard for API authorization. Understanding it matters because:
- FastAPI's security system is built on OAuth2 concepts
- "Login with Google/GitHub" requires OAuth2
- Many third-party APIs use OAuth2 for access control
- It's the foundation of OpenID Connect (OIDC) for authentication

---

## 3. When Should I Use It?

- **Social login** — Let users sign in with Google, GitHub, etc.
- **Third-party API access** — When your app needs to access external APIs on behalf of users
- **API authorization** — When external apps need to access your API on behalf of your users
- **FastAPI's OAuth2PasswordBearer** — FastAPI uses OAuth2 concepts for its built-in security

---

## 4. When Should I NOT Use It?

- **Simple username/password auth** — You don't need the full OAuth2 flow for basic login. FastAPI uses OAuth2 terminology but implements a simpler flow
- **Server-to-server with known parties** — API keys or mutual TLS may be simpler
- **When you don't need third-party access** — If only your own frontend accesses your API, the full OAuth2 grant types are overkill

---

## 5. How Does It Work?

### Key Concepts

- **Resource Owner** — The user who owns the data
- **Client** — The application requesting access (your frontend, a mobile app)
- **Authorization Server** — Issues tokens (Google, GitHub, or your own)
- **Resource Server** — Your API that serves protected data

### Grant Types

| Grant Type | Use Case |
|---|---|
| **Authorization Code** | Web apps with a backend (most secure) |
| **Authorization Code + PKCE** | Mobile/SPA apps (public clients) |
| **Client Credentials** | Server-to-server (no user involved) |
| **Resource Owner Password** | Legacy; not recommended for new apps |
| **Device Code** | Smart TVs, CLI tools |

### FastAPI's OAuth2PasswordBearer

FastAPI provides `OAuth2PasswordBearer`, which:
1. Expects a login endpoint that accepts username/password
2. Returns a token
3. Subsequent requests send the token in `Authorization: Bearer <token>`

This is the **Resource Owner Password** flow — simple but not suitable for third-party access. For DevFlow's own frontend, it works well. For social login, you'll use the Authorization Code flow.

---

## 6. How Does It Fit Into DevFlow?

### Primary Authentication (Password-Based)

DevFlow uses FastAPI's OAuth2 password bearer for its own login system:
1. User sends email + password to `POST /auth/login`
2. Server validates credentials and returns tokens
3. Client includes access token in subsequent requests

### Social Login (Optional Extension)

For "Login with GitHub" or "Login with Google":
1. Frontend redirects to Google/GitHub's authorization URL
2. User approves access
3. Provider redirects back with an authorization code
4. Backend exchanges code for tokens
5. Backend creates/links user account

---

## 7. Common Mistakes

### Confusing OAuth2 with Authentication

OAuth2 is an **authorization** framework. It doesn't define how to authenticate users — that's OpenID Connect (built on top of OAuth2).

### Implementing the Full OAuth2 Server Unnecessarily

Unless you're building an API platform that third parties will consume, you don't need a full OAuth2 authorization server.

### Not Using PKCE for Public Clients

SPAs and mobile apps cannot keep a client secret. Always use PKCE (Proof Key for Code Exchange) for public clients.

### Storing OAuth2 Tokens Insecurely

Provider tokens (Google, GitHub) should be encrypted at rest if stored.

---

## 8. Production Considerations

- **State parameter** — Always use the `state` parameter to prevent CSRF in OAuth2 flows
- **Token storage** — Encrypt provider tokens at rest
- **Scope minimization** — Request only the scopes you need
- **Provider rate limits** — Respect rate limits on token exchanges and user info endpoints
- **Account linking** — Handle the case where a user signs up with email and later tries to log in with Google using the same email

---

## 9. Prerequisites

- HTTP redirects and query parameters
- JWT basics (see `04-authentication/jwt.md`)
- Understanding of authentication vs. authorization

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain OAuth2's purpose and key concepts
- [ ] Describe the Authorization Code flow
- [ ] Use FastAPI's OAuth2PasswordBearer
- [ ] Understand when full OAuth2 is needed vs. simple token auth
- [ ] Plan a social login integration
