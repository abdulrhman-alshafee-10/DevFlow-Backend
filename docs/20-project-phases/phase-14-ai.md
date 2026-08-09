# Phase 14 — AI Integration

## Objective

Integrate LLM APIs to provide AI-powered features: task analysis, project summarization, smart suggestions, and a conversational assistant. Responses stream to the client via SSE for a responsive user experience.

---

## Concepts Learned

- LLM API integration (OpenAI/Anthropic)
- Prompt engineering and template design
- Context gathering from application data
- Response streaming via Server-Sent Events
- Cost management and rate limiting
- Basic RAG (Retrieval-Augmented Generation)
- AI security (prompt injection, data privacy)

**Relevant docs**:
- `14-ai/ai-architecture.md`
- `10-realtime/server-sent-events.md`

---

## Features After This Phase

- [ ] Analyze a task (break down complexity, identify risks, estimate effort)
- [ ] Summarize a project (overall status, blockers, recommendations)
- [ ] Suggest subtasks for a task
- [ ] AI chat assistant (answer questions about project/tasks)
- [ ] Stream AI responses via SSE
- [ ] Rate limiting on AI endpoints (cost control)
- [ ] Prompt templates for each AI feature
- [ ] Context injection from project data

---

## API Endpoints

| Method | Path | Description | Auth | Response |
|---|---|---|---|---|
| POST | `/api/v1/ai/tasks/{id}/analyze` | Analyze a task | Yes | SSE stream |
| POST | `/api/v1/ai/projects/{id}/summarize` | Summarize project | Yes | SSE stream |
| POST | `/api/v1/ai/tasks/{id}/suggest-subtasks` | Suggest subtasks | Yes | JSON |
| POST | `/api/v1/ai/chat` | Chat with AI assistant | Yes | SSE stream |

### Request/Response

**POST /ai/tasks/{id}/analyze** (SSE Response)
```
Request:  { "focus": "risks" }  (optional focus area)
Response: text/event-stream
  data: {"token": "Based"}
  data: {"token": " on"}
  data: {"token": " the"}
  ...
  data: {"done": true, "usage": {"prompt_tokens": 500, "completion_tokens": 200}}
```

**POST /ai/chat** (SSE Response)
```
Request:  { "message": "What are the blockers for the release?", "project_id": "..." }
Response: text/event-stream (streamed response)
```

---

## Implementation Architecture

```
1. Request received at AI endpoint
2. Authorization check (project member)
3. Rate limit check (AI-specific limits)
4. Context gathering:
   a. Load task/project details from DB
   b. Load recent comments
   c. Load related tasks
   d. (Optional) RAG: Search for relevant context using embeddings
5. Prompt construction:
   a. System prompt (role, constraints, output format)
   b. Context (project data, task data)
   c. User prompt (the actual question/request)
6. LLM API call (with streaming)
7. Stream tokens to client via SSE
8. Log usage (tokens, cost, duration)
```

---

## Completion Checklist

- [ ] Created AI service with provider abstraction
- [ ] Created prompt templates for each feature
- [ ] Context gathering from database (tasks, comments, project info)
- [ ] SSE streaming endpoint implementation
- [ ] OpenAI/Anthropic API integration with httpx
- [ ] Rate limiting on AI endpoints (20 req/hour per user)
- [ ] Usage logging (tokens, cost)
- [ ] Error handling (API failures, timeouts, rate limits)
- [ ] Input sanitization for prompt injection prevention
- [ ] Tests for AI endpoints (mocked LLM responses)
- [ ] Optional: Basic RAG with pgvector
