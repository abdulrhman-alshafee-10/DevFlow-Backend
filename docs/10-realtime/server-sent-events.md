# Server-Sent Events (SSE)

## 1. What Is It?

Server-Sent Events (SSE) is a technology for server-to-client streaming over HTTP. Unlike WebSockets (bidirectional), SSE is unidirectional — the server pushes events to the client. It uses a standard HTTP connection with `text/event-stream` content type.

---

## 2. Why Does It Matter?

SSE is simpler than WebSockets and perfect for:
- **Notifications** — Push notifications without polling
- **AI streaming** — Stream LLM responses token by token
- **Live feeds** — Activity logs, dashboard updates
- **Progress updates** — File upload progress, report generation status

### SSE vs. WebSockets

| Feature | SSE | WebSockets |
|---|---|---|
| Direction | Server → Client only | Bidirectional |
| Protocol | HTTP | WebSocket (WS/WSS) |
| Reconnection | Automatic (built-in) | Manual |
| Complexity | Simpler | More complex |
| Browser support | Native EventSource API | Native WebSocket API |
| Load balancers | Works with standard HTTP | Needs WebSocket support |

---

## 6. How Does It Fit Into DevFlow?

| Feature | Protocol | Why |
|---|---|---|
| Chat messages | WebSocket | Bidirectional — client sends messages too |
| Notifications | SSE or WebSocket | Unidirectional — server pushes only |
| AI response streaming | SSE | Stream tokens as they're generated |
| Task updates | WebSocket | Bidirectional — client actions trigger updates |
| Progress indicators | SSE | Server reports progress |

### AI Streaming with SSE

When a user asks the AI assistant to analyze a task, the response streams token-by-token:

```
Client: POST /ai/analyze  (request)
Server: 200 OK, Content-Type: text/event-stream

data: {"token": "Based"}
data: {"token": " on"}
data: {"token": " the"}
data: {"token": " task"}
data: {"token": " description"}
...
data: {"token": "[DONE]"}
```

This provides a much better UX than waiting 10 seconds for the full response.

---

## What I Should Be Able to Do Afterward

- [ ] Implement SSE endpoints in FastAPI using StreamingResponse
- [ ] Stream AI/LLM responses to clients
- [ ] Choose between SSE and WebSockets for different features
- [ ] Handle client disconnections in SSE
- [ ] Implement reconnection with Last-Event-ID
