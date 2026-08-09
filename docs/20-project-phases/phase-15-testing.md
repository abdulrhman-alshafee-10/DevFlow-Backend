# Phase 15 — Comprehensive Testing

## Objective

Build a comprehensive test suite that covers all features, edge cases, and security scenarios. This phase isn't about adding new features — it's about ensuring everything built so far works correctly and catching bugs before they reach production.

---

## Concepts Learned

- Test organization and structure
- Fixture design for complex test data
- Test factories with factory-boy
- Mocking external services
- Testing authentication and authorization systematically
- Testing WebSocket connections
- Testing background jobs
- Code coverage analysis
- Testing security scenarios

**Relevant docs**:
- `16-testing/testing-overview.md`

---

## Test Categories and Scenarios

### Unit Tests (Fast, No DB)

**Services:**
- Password hashing and verification
- JWT creation and validation
- Permission checking logic
- Token generation (verification, reset)
- Business rule validation
- Rate limit calculation

**Utilities:**
- File type detection
- Filename sanitization
- Pagination parameter parsing
- Search query parsing

### Integration Tests (With Test DB)

**Repositories:**
- User CRUD operations
- Task filtering, sorting, pagination
- Organization member queries
- Notification queries
- Search queries (full-text search)

**Services with DB:**
- Task creation with all side effects (audit log, notification)
- Invitation flow (send → accept → membership created)
- Password reset flow (request → token → reset → sessions revoked)

### API Tests (Full HTTP Cycle)

**For each endpoint, test:**
- Happy path (valid request → expected response)
- Validation errors (invalid input → 422)
- Authentication required (no token → 401)
- Authorization denied (wrong role → 403)
- Resource not found (invalid ID → 404)
- Conflict errors (duplicate data → 409)

### Authentication Test Scenarios

- [ ] Register → login → access protected resource
- [ ] Access token expiration → refresh → continue
- [ ] Refresh token rotation → old token invalid
- [ ] Refresh token reuse → all tokens revoked
- [ ] Password change → all sessions invalidated
- [ ] Password reset → all sessions invalidated
- [ ] Account lockout after failed attempts
- [ ] Email verification flow end-to-end

### Authorization Test Matrix

Test every endpoint with every role:

```
Endpoint                    | OWNER | ADMIN | MANAGER | MEMBER | VIEWER | No Auth
POST /organizations         |   ✓   |   ✓   |    ✓    |   ✓    |   ✓    |   401
DELETE /organizations/{id}  |   ✓   |  403  |   403   |  403   |  403   |   401
POST /projects              |   ✓   |   ✓   |   403   |  403   |  403   |   401
PATCH /tasks/{id}           |   ✓   |   ✓   |    ✓    |  own   |  403   |   401
DELETE /comments/{id}       |   ✓   |   ✓   |   own   |  own   |  403   |   401
```

### Security Test Scenarios

- [ ] Cross-organization data access (must be denied)
- [ ] Cross-project data access (must be denied)
- [ ] IDOR testing (accessing resources by guessing IDs)
- [ ] Mass assignment (sending fields that shouldn't be user-settable)
- [ ] SQL injection attempts (handled by SQLAlchemy)
- [ ] XSS payloads in text fields (stored but not executed)
- [ ] Oversized request bodies
- [ ] Invalid file type uploads
- [ ] Rate limit enforcement
- [ ] Email enumeration prevention (login, forgot-password)

### WebSocket Tests

- [ ] Connection with valid token
- [ ] Connection rejected with invalid token
- [ ] Message broadcast to room subscribers
- [ ] Connection cleanup on disconnect
- [ ] Message format validation

---

## Coverage Target

- **Minimum**: 80% code coverage
- **Critical paths**: 100% coverage on auth, authorization, and payment-related code
- **Focus**: Coverage is a guide, not a goal. 80% meaningful coverage beats 100% trivial coverage.

---

## Completion Checklist

- [ ] Created test factories for all models (User, Org, Project, Task, etc.)
- [ ] Created shared fixtures for common test scenarios
- [ ] Unit tests for all service methods
- [ ] Integration tests for all repository methods
- [ ] API tests for all endpoints with all roles
- [ ] Authentication flow tests (end-to-end)
- [ ] Authorization matrix fully tested
- [ ] Security scenario tests
- [ ] WebSocket tests
- [ ] Background job tests
- [ ] Code coverage report generated
- [ ] Coverage above 80%
- [ ] All tests pass in CI/CD pipeline
