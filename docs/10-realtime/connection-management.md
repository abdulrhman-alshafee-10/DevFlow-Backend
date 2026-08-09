# Connection Management

## 1. What Is It?

Connection management is the system that tracks active WebSocket connections, organizes them into rooms/channels, and handles broadcasting messages to the right recipients. It's the backbone of real-time features.

---

## 2. Why Does It Matter?

Without a connection manager:
- You can't broadcast a task update to everyone viewing a project
- You can't send a notification to a specific user
- Disconnected clients leave orphaned connections (memory leak)
- You can't scale across multiple server instances

---

## 5. How Does It Work?

### Connection Manager Design

```
ConnectionManager:
  connections:
    by_user: { user_id: [websocket1, websocket2, ...] }
    by_room: { "project:123:tasks": [websocket1, websocket3, ...] }

  Methods:
    connect(websocket, user_id, room)
    disconnect(websocket)
    broadcast_to_room(room, message)
    send_to_user(user_id, message)
    get_room_members(room)
```

### Room Naming Convention

```
project:{project_id}:tasks     → Task updates for a project
notifications:{user_id}        → Personal notifications
chat:{room_id}                 → Chat room
presence:{project_id}          → Online presence for a project
```

### Scaling Across Servers

A single server's ConnectionManager only knows about its own connections. For multi-server deployments, use Redis Pub/Sub:

```
Server A: User creates a task
    → Publishes to Redis channel "project:123:tasks"

Server B: Subscribed to "project:123:tasks"
    → Receives event
    → Broadcasts to its local WebSocket connections
```

---

## What I Should Be Able to Do Afterward

- [ ] Implement a connection manager that tracks users and rooms
- [ ] Handle connect/disconnect lifecycle correctly
- [ ] Broadcast messages to specific rooms
- [ ] Send messages to specific users
- [ ] Scale across servers using Redis Pub/Sub
- [ ] Clean up connections on disconnect (prevent memory leaks)
