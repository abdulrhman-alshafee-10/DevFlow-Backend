# Testing Overview

## 1. What Is It?

Testing is the practice of verifying that your code behaves correctly through automated checks. A comprehensive test suite catches bugs before they reach production, enables confident refactoring, and serves as living documentation for how your code should behave.

---

## 2. Why Does It Matter?

Without tests:
- Every change risks breaking existing features
- Refactoring is terrifying (you don't know what you'll break)
- Bug reports from production are your only feedback loop
- New team members can't verify their changes are safe
- Deployment is a gamble

---

## Testing Pyramid

```
         ╱╲
        ╱  ╲         E2E Tests (few)
       ╱    ╲         - Full system tests
      ╱──────╲
     ╱        ╲       Integration Tests (some)
    ╱          ╲       - API tests, DB tests
   ╱────────────╲
  ╱              ╲     Unit Tests (many)
 ╱                ╲     - Service logic, utilities
╱──────────────────╲
```

### Test Types in DevFlow

| Type | What It Tests | Speed | Database? |
|---|---|---|---|
| **Unit** | Service logic, utilities, validators | Fast | No (mocked) |
| **Integration** | Repositories, database queries | Medium | Yes (test DB) |
| **API** | Full HTTP request/response cycle | Medium | Yes (test DB) |
| **WebSocket** | WebSocket connections and messaging | Medium | Yes |
| **Security** | Auth bypass, authorization, injection | Medium | Yes |

---

## DevFlow Testing Strategy

### What Must Be Tested

**Authentication (critical)**:
- Registration with valid/invalid data
- Login with correct/incorrect credentials
- Token refresh with valid/expired/revoked tokens
- Password reset flow
- Email verification flow
- Brute-force protection triggers
- Logout revokes tokens

**Authorization (critical)**:
- Each endpoint with each role (OWNER, ADMIN, MANAGER, MEMBER, VIEWER)
- Cross-organization access denied
- Resource ownership checks
- Role escalation prevention

**CRUD operations**:
- Create with valid/invalid data
- Read existing/non-existent resources
- Update with partial data
- Delete with proper cleanup

**Business rules**:
- Task status transitions
- Invitation flow (send, accept, reject, expire)
- Organization membership limits
- Project archival prevents task creation

**Edge cases**:
- Concurrent updates to the same resource
- Empty collections
- Maximum field lengths
- Unicode and special characters

---

## Tools and Setup

| Tool | Purpose |
|---|---|
| **pytest** | Test framework |
| **pytest-asyncio** | Async test support |
| **httpx.AsyncClient** | FastAPI test client |
| **factory-boy** | Test data factories |
| **Faker** | Realistic test data |
| **pytest-cov** | Code coverage reporting |

### Test Database

Use a separate PostgreSQL database for tests:
- Create fresh schema before each test session
- Use transactions that rollback after each test (fast cleanup)
- Or truncate tables between tests

### Fixtures

```
conftest.py fixtures:
  - db_session → Async database session (rolled back after test)
  - client → httpx.AsyncClient with test app
  - authenticated_client → Client with auth headers
  - user_factory → Creates test users
  - org_factory → Creates test organizations
  - task_factory → Creates test tasks
```

---

## What I Should Be Able to Do Afterward

- [ ] Set up pytest with async support for FastAPI
- [ ] Write unit tests for service layer logic
- [ ] Write integration tests for database operations
- [ ] Write API tests for endpoints
- [ ] Create test fixtures and factories
- [ ] Test authentication and authorization thoroughly
- [ ] Generate and interpret code coverage reports
- [ ] Mock external services (email, AI APIs, Redis)
