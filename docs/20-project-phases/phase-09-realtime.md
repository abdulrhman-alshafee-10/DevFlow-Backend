# Phase 9 — Real-Time Features

## Objective

Add real-time capabilities to DevFlow using WebSockets and Server-Sent Events. Users see live task updates, receive instant notifications, and can chat in real-time without refreshing the page.

---

## Concepts Learned

- WebSocket connections in FastAPI
- WebSocket authentication
- Connection management (rooms, channels)
- Broadcasting with Redis Pub/Sub
- Server-Sent Events for one-way streaming
- Connection lifecycle management
- Scaling real-time across multiple server instances

**Relevant docs**:
- `10-realtime/websockets.md`
- `10-realtime/server-sent-events.md`

---

## Features After This Phase

- [ ] WebSocket endpoint for project task updates
- [ ] WebSocket endpoint for notifications
- [ ] WebSocket authentication via token
- [ ] Connection manager with room/channel support
- [ ] Redis Pub/Sub for cross-server broadcasting
- [ ] SSE endpoint for notification streaming
- [ ] Live task updates when tasks are created/updated/deleted
- [ ] Live notification delivery

---

## API Endpoints (WebSocket & SSE)

| Protocol | Path | Description | Auth |
|---|---|---|---|
| WS | `/ws/projects/{project_id}/tasks` | Live task updates | Token in query param |
| WS | `/ws/notifications` | Real-time notifications | Token in query param |
| WS | `/ws/chat/{room_id}` | Chat room | Token in query param |
| SSE | `/api/v1/notifications/stream` | Notification stream | Bearer token |

### WebSocket Message Format

```json
{
  "type": "task_updated",
  "payload": {
    "task_id": "...",
    "changes": {"status": "in_progress"},
    "actor": {"id": "...", "name": "Alice"}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Testing Requirements

- WebSocket connection with valid token succeeds
- WebSocket connection without token rejected
- WebSocket connection with expired token rejected
- Task updates broadcast to all project room subscribers
- Notifications delivered to correct user's WebSocket
- Disconnection cleanup works (no memory leaks)
- Messages are valid JSON with expected structure

---

## Completion Checklist

- [ ] Created WebSocket connection manager
- [ ] Created WebSocket authentication (token from query params)
- [ ] Created `/ws/projects/{id}/tasks` endpoint
- [ ] Created `/ws/notifications` endpoint
- [ ] Integrated Redis Pub/Sub for broadcasting
- [ ] Task service publishes events on create/update/delete
- [ ] Notification service publishes events on creation
- [ ] Created SSE endpoint for notifications
- [ ] Connection lifecycle properly managed (connect/disconnect/cleanup)
- [ ] WebSocket tests pass
- [ ] Load tested with multiple simultaneous connections
