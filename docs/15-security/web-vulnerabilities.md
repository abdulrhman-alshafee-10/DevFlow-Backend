# CORS, CSRF, XSS, and SQL Injection

## CORS (Cross-Origin Resource Sharing)

### What Is It?
CORS is a browser security mechanism that restricts which domains can make requests to your API. By default, browsers block requests from a different origin than the server.

### DevFlow Configuration
- **Development**: Allow `http://localhost:3000` (frontend dev server)
- **Production**: Allow only your production frontend domain
- **Never use**: `allow_origins=["*"]` in production (allows any website to call your API)

### Key Settings
```
origins: ["https://app.devflow.com"]
methods: ["GET", "POST", "PUT", "PATCH", "DELETE"]
headers: ["Authorization", "Content-Type"]
credentials: true  (needed for cookies)
```

---

## CSRF (Cross-Site Request Forgery)

### What Is It?
CSRF tricks a logged-in user's browser into making requests to your API. If a user is logged into DevFlow and visits a malicious site, that site could make requests to DevFlow using the user's cookies.

### Protection
- **SameSite cookies** — Set `SameSite=Lax` or `SameSite=Strict` on all cookies
- **CSRF tokens** — For any form submissions (less relevant for pure API backends)
- **Custom headers** — Require `X-Requested-With` or similar custom header
- **Check Origin header** — Verify the request's Origin matches your domain

### DevFlow Approach
DevFlow uses JWT in the Authorization header (not cookies) for API auth, which is inherently CSRF-resistant. The refresh token is stored in a `SameSite=Lax; HttpOnly; Secure` cookie, which provides CSRF protection.

---

## XSS (Cross-Site Scripting)

### What Is It?
XSS occurs when an attacker injects malicious JavaScript into your application that executes in other users' browsers. In a backend API context, XSS happens when user input is stored and returned without sanitization.

### Types
- **Stored XSS** — Malicious script stored in the database (e.g., in a task description)
- **Reflected XSS** — Script in a URL parameter reflected in the response
- **DOM-based XSS** — Frontend vulnerability (not a backend concern)

### Protection
- **Never trust user input** — Validate and sanitize all text fields
- **Content-Security-Policy header** — Restrict what scripts can execute
- **X-Content-Type-Options: nosniff** — Prevent MIME type sniffing
- **Escape HTML in responses** — If returning HTML, escape user-generated content
- **JSON APIs are safer** — JSON responses are not executed as HTML by default

### DevFlow Approach
DevFlow is a JSON API — responses are not rendered as HTML. However:
- Task descriptions, comments, and project names could contain malicious content
- Sanitize HTML-like content on input
- The frontend must escape content when rendering

---

## SQL Injection

### What Is It?
SQL injection occurs when user input is inserted directly into SQL queries, allowing attackers to execute arbitrary SQL. This can expose, modify, or delete all data in your database.

### Protection
SQLAlchemy prevents SQL injection by default through **parameterized queries**. When you use SQLAlchemy's query builder, parameters are always escaped:

```
# SAFE — SQLAlchemy parameterizes this
select(User).where(User.email == user_input)

# DANGEROUS — Raw SQL with string formatting
text(f"SELECT * FROM users WHERE email = '{user_input}'")
```

### DevFlow Rules
- **Never** use f-strings or `.format()` in SQL queries
- **Always** use SQLAlchemy's query builder or `text()` with bound parameters
- **Never** pass user input to `text()` without parameterization

---

## What I Should Be Able to Do Afterward

- [ ] Configure CORS properly for development and production
- [ ] Prevent CSRF with SameSite cookies and proper token handling
- [ ] Understand XSS vectors and how JSON APIs mitigate them
- [ ] Explain why SQLAlchemy prevents SQL injection
- [ ] Set appropriate security headers
