# OpenID Connect (OIDC)

## 1. What Is It?

OpenID Connect (OIDC) is an identity layer built on top of OAuth2. While OAuth2 handles **authorization** (granting access to resources), OIDC adds **authentication** (verifying who the user is). It's the protocol that powers "Sign in with Google" and similar identity features.

---

## 2. Why Does It Matter?

- It's the standard for identity federation (using external identity providers)
- Understanding OIDC helps you implement social login correctly
- Many enterprise applications require OIDC for single sign-on (SSO)
- It defines standard claims (name, email, profile) and discovery mechanisms

---

## 3. When Should I Use It?

- **Social login** — Sign in with Google, GitHub, Microsoft, etc.
- **Enterprise SSO** — When organizations want to use their own identity provider
- **Identity federation** — When multiple services share a common identity

---

## 4. When Should I NOT Use It?

- **Simple apps with their own user database** — DevFlow's primary auth doesn't need OIDC
- **Service-to-service auth** — Use OAuth2 Client Credentials or mutual TLS
- **When you don't need third-party identity** — Adding OIDC complexity without a use case

---

## 5. How Does It Work?

### OIDC Adds to OAuth2

| OAuth2 | OIDC |
|---|---|
| Access Token | ID Token (JWT with user claims) |
| Authorization endpoint | Same, with `openid` scope |
| Token endpoint | Same, returns ID Token |
| No standard user info | UserInfo endpoint with standard claims |
| No discovery | `.well-known/openid-configuration` |

### ID Token Claims

```json
{
  "iss": "https://accounts.google.com",
  "sub": "110169484474386276334",
  "email": "user@gmail.com",
  "email_verified": true,
  "name": "John Doe",
  "picture": "https://...",
  "iat": 1705310400,
  "exp": 1705312200
}
```

### OIDC Flow (for Social Login)

```
1. User clicks "Sign in with Google"
2. Redirect to Google's authorization endpoint with scope=openid email profile
3. User authenticates with Google and consents
4. Google redirects back with authorization code
5. Backend exchanges code for tokens (access token + ID token)
6. Backend validates ID token
7. Backend extracts user info (email, name)
8. Backend creates or links local user account
9. Backend issues its own access/refresh tokens
```

---

## 6. How Does It Fit Into DevFlow?

OIDC is an **optional extension** for DevFlow. The core authentication is password-based. Social login adds convenience:

- **Account creation** — If a user signs in with Google, create an account using their Google email and name
- **Account linking** — If a user already has a DevFlow account with the same email, link the Google identity
- **No password needed** — Users who sign up with Google don't need a DevFlow password

---

## 7. Common Mistakes

### Not Validating the ID Token

The ID token must be validated (signature, issuer, audience, expiration). Never trust it blindly.

### Confusing OAuth2 and OIDC

OAuth2 alone doesn't tell you who the user is. You need OIDC (or the provider's proprietary user info endpoint) for that.

### Not Handling Account Linking

What if a user registers with email first, then tries to sign in with Google using the same email? You need a linking strategy.

---

## 8. Production Considerations

- **Provider-specific quirks** — Each provider (Google, GitHub, Microsoft) has slight differences
- **Token refresh** — Provider access tokens expire; refresh them if you need ongoing API access
- **Consent screen** — Users see what data you're requesting; minimize scopes
- **Provider outages** — Have a fallback if a provider is down

---

## 9. Prerequisites

- OAuth2 (see `04-authentication/oauth2.md`)
- JWT (see `04-authentication/jwt.md`)

---

## 10. What I Should Be Able to Do Afterward

- [ ] Explain the difference between OAuth2 and OIDC
- [ ] Describe the OIDC flow for social login
- [ ] Validate an ID token
- [ ] Plan a social login feature with account linking
