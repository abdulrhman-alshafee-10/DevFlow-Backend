# AI Architecture

## 1. What Is It?

AI integration in DevFlow connects the application to Large Language Model (LLM) APIs to provide intelligent features: task analysis, project summarization, smart suggestions, and a conversational assistant.

---

## 2. Why Does It Matter?

AI features differentiate DevFlow from basic task managers. They provide:
- **Task analysis** — Automatically break down tasks, estimate complexity, identify risks
- **Project insights** — Summarize project status, identify bottlenecks
- **Smart suggestions** — Suggest assignees, priorities, related tasks
- **Natural language search** — Ask questions about your project in plain English
- **Content generation** — Draft task descriptions, meeting summaries

---

## 5. How Does It Work?

### Integration Architecture

```
Client Request → FastAPI → AI Service → LLM Provider API
                              │
                              ├── Prompt construction
                              ├── Context gathering (from DB)
                              ├── API call (with retry/timeout)
                              ├── Response parsing
                              └── Streaming to client (SSE)
```

### Key Components

1. **AI Service** — Orchestrates AI operations, constructs prompts, manages context
2. **Prompt Templates** — Structured templates for different AI tasks
3. **Context Provider** — Gathers relevant data from the database to include in prompts
4. **Response Parser** — Extracts structured data from LLM responses
5. **Streaming Handler** — Streams responses token-by-token via SSE

### DevFlow AI Features

| Feature | Endpoint | Method |
|---|---|---|
| Analyze task | `POST /ai/tasks/{id}/analyze` | Streaming SSE |
| Summarize project | `POST /ai/projects/{id}/summarize` | Streaming SSE |
| Suggest subtasks | `POST /ai/tasks/{id}/suggest-subtasks` | JSON response |
| Smart search | `POST /ai/search` | JSON response |
| Chat assistant | `POST /ai/chat` | Streaming SSE |

---

## LLM Integration

### Provider Abstraction

Create an abstraction layer so you can switch between providers:
- **OpenAI** — GPT-4, GPT-3.5
- **Anthropic** — Claude
- **Self-hosted** — Ollama, vLLM

### Prompt Engineering

Structure prompts with:
- **System prompt** — Role and constraints
- **Context** — Relevant project/task data from the database
- **User prompt** — The user's actual question or request
- **Output format** — JSON schema for structured responses

---

## RAG (Retrieval-Augmented Generation)

RAG enhances AI responses by providing relevant context from your data:

```
1. User asks: "What are the blockers for the mobile release?"
2. System embeds the question into a vector
3. System searches for similar task descriptions/comments (vector search)
4. System includes the top matches as context in the LLM prompt
5. LLM generates an answer grounded in actual project data
```

### RAG Components
- **Embeddings** — Convert text to vectors (OpenAI embeddings API)
- **Vector store** — Store and search vectors (pgvector extension for PostgreSQL)
- **Retriever** — Find relevant documents for a query
- **Generator** — LLM that generates a response using retrieved context

---

## 6. How Does It Fit Into DevFlow?

AI features are added in Phase 14, after all core features are built. This is intentional:
- AI needs data to work with (tasks, comments, projects)
- AI features depend on search, background jobs, and SSE
- The AI service uses the same repository/service architecture as other features

---

## 7. Common Mistakes

### Not Setting Cost Limits
LLM API calls cost money. Without limits, a user could run up a large bill. Implement per-user rate limiting and cost tracking.

### Not Streaming Long Responses
A 30-second wait for an AI response is terrible UX. Stream tokens via SSE.

### Trusting LLM Output
LLMs can hallucinate. Never use LLM output for security decisions, database queries, or financial calculations without validation.

### Not Handling API Failures
LLM APIs have rate limits, outages, and timeouts. Implement retries, fallbacks, and graceful degradation.

### Prompt Injection
Users can craft inputs that override your system prompt. Sanitize inputs and use separate system/user message roles.

---

## 8. Production Considerations

- **Cost management** — Track API usage per user/organization; set spending limits
- **Latency** — LLM calls take 1-30 seconds; always stream and show progress
- **Rate limiting** — Respect provider rate limits; queue excess requests
- **Caching** — Cache identical requests (same prompt → same response) with TTL
- **Monitoring** — Track token usage, response times, and error rates
- **Privacy** — Don't send sensitive data (passwords, PII) to LLM APIs
- **Fallbacks** — If the AI service is down, the rest of the app should work fine

---

## What I Should Be Able to Do Afterward

- [ ] Integrate an LLM API (OpenAI/Anthropic) into FastAPI
- [ ] Stream AI responses via SSE
- [ ] Implement prompt templates with context injection
- [ ] Build a basic RAG pipeline with pgvector
- [ ] Handle AI API errors, rate limits, and timeouts
- [ ] Secure AI endpoints against prompt injection and cost abuse
