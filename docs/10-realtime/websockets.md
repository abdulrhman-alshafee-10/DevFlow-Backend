# WebSockets

## 1. What Is It?

WebSockets provide a full-duplex, persistent communication channel between client and server. Unlike HTTP (request-response), WebSockets allow the server to push data to the client at any time without the client asking.

---

## 2. Why Does It Matter?

Some features can't work with traditional HTTP:
- **Real-time chat** — Messages must appear instantly
- **Live task updates** — When someone changes a task, everyone sees it immediately
- **Online presence** — Who's currently viewing this project
- **Collaborative editing** — Multiple users working on the same content

---

## 5. How Does It Work?

### Connection Lifecycle

```
1. Client sends HTTP upgrade request
2. Server accepts and upgrades to WebSocket
3. Bidirectional messages flow freely
4. Either side can close the connection
```

### FastAPI WebSocket Endpoints

FastAPI has built-in WebSocket support. You define WebSocket endpoints alongside regular HTTP endpoints.

### Connection Management

A connection manager tracks all active connections:
- **Connect** — Add connection to a room/channel
- **Disconnect** — Remove connection, clean up
- **Broadcast** — Send message to all connections in a room
- **Send to user** — Send message to a specific user's connections

### DevFlow WebSocket Channels

```
/ws/notifications          → Personal notifications
/ws/projects/{id}/tasks    → Live task updates for a project  
/ws/chat/{room_id}         → Real-time chat
```

---

## 6. How Does It Fit Into DevFlow?

| Feature | WebSocket Channel | Payload |
|---|---|---|
| Task created/updated/deleted | `projects/{id}/tasks` | Task data + action type |
| New comment | `projects/{id}/tasks` | Comment data |
| Chat message | `chat/{room_id}` | Message data |
| User online/offline | `projects/{id}/presence` | User ID + status |
| Notifications | `notifications` | Notification data |

### Scaling WebSockets

WebSocket connections are per-server. To broadcast across multiple server instances, use Redis Pub/Sub:

```
Server A receives task update
    ↓
Publishes to Redis channel "project:123:tasks"
    ↓
Server B subscribed to channel receives the event
    ↓
Server B broadcasts to its connected clients
```

---

## 7. Common Mistakes

### Not Authenticating WebSocket Connections
WebSockets don't send the Authorization header after the initial handshake. Authenticate during the connection handshake using query parameters or the first message.

### Not Handling Disconnections
Clients disconnect unexpectedly (network issues, browser closed). Always handle disconnection cleanup.

### Memory Leaks from Untracked Connections
If you store connections but don't remove them on disconnect, memory grows unbounded.

### Blocking the Event Loop in WebSocket Handlers
Long-running operations in a WebSocket handler block all other WebSocket messages.

---

## What I Should Be Able to Do Afterward

- [ ] Create WebSocket endpoints in FastAPI
- [ ] Authenticate WebSocket connections
- [ ] Build a connection manager for rooms/channels
- [ ] Broadcast messages to connected clients
- [ ] Scale WebSockets across multiple servers with Redis Pub/Sub
- [ ] Handle disconnections and cleanup gracefully
