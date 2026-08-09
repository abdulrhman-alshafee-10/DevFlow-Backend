# WebSocket Authentication

## 1. What Is It?

WebSocket connections don't support the `Authorization` header after the initial handshake. This means the standard JWT-in-header approach doesn't work for WebSockets. You need an alternative authentication strategy.

---

## 2. Why Does It Matter?

Without WebSocket authentication, anyone who can guess a WebSocket URL can:
- Listen to private project updates
- Read other users' notifications
- Send messages as anyone in chat rooms

---

## Authentication Strategies for WebSockets

| Strategy | How | Security |
|---|---|---|
| **Token in query parameter** | `ws://host/ws?token=jwt` | Token in server logs/URL; use short-lived tokens |
| **Token in first message** | Connect, then send `{"type": "auth", "token": "jwt"}` | Better; no token in URL |
| **Cookie-based** | Token in an HttpOnly cookie sent during handshake | Best browser security; limited flexibility |
| **Ticket system** | Request a short-lived ticket via REST, use it to connect | Best overall; ticket expires in 30 seconds |

### DevFlow Approach: Token in Query Parameter

The simplest approach. Pass the access token as a query parameter:

```
ws://localhost:8000/ws/notifications?token=eyJhbGc...
```

The server extracts and validates the token during the WebSocket handshake. If invalid, the connection is rejected immediately.

**Security mitigation**: Access tokens are short-lived (15 min), limiting exposure if logged.

---

## Connection Lifecycle with Auth

```
1. Client obtains access token via login
2. Client opens WebSocket: ws://host/ws/notifications?token=<jwt>
3. Server extracts token from query params
4. Server validates JWT (signature, expiration)
5. Server loads user from token claims
6. If valid: WebSocket connection accepted
7. If invalid: WebSocket connection rejected (close code 4001)
8. Client receives messages as long as connection is open
9. If token expires during connection: optionally re-authenticate or close
```

---

## What I Should Be Able to Do Afterward

- [ ] Authenticate WebSocket connections using query parameter tokens
- [ ] Reject unauthorized WebSocket connections during handshake
- [ ] Understand the tradeoffs of different WebSocket auth strategies
- [ ] Handle token expiration during long-lived connections
