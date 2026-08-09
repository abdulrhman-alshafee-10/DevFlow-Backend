# PostgreSQL Full-Text Search

## 1. What Is It?

PostgreSQL has built-in full-text search (FTS) that goes beyond simple LIKE queries. It supports stemming (matching "running" when searching "run"), ranking (ordering by relevance), and highlighting (showing matching fragments). It's powerful enough for most applications without adding Elasticsearch.

---

## 2. Why Does It Matter?

DevFlow users need to search for tasks, projects, and comments by text. Simple `ILIKE '%query%'` has limitations:
- No relevance ranking
- No stemming (searching "deploy" won't find "deployment")
- No phrase matching
- Poor performance on large datasets (can't use indexes)

PostgreSQL FTS solves all of these with a GIN index.

---

## 5. How Does It Work?

### Core Concepts

- **tsvector** — A processed text document (tokenized, stemmed, weighted)
- **tsquery** — A processed search query
- **GIN index** — An index on tsvector columns for fast searching
- **Ranking** — `ts_rank()` orders results by relevance
- **Highlighting** — `ts_headline()` shows matching fragments

### DevFlow Search Implementation

```
Step 1: Add a tsvector column to searchable tables
Step 2: Create a GIN index on the tsvector column  
Step 3: Update the tsvector on INSERT/UPDATE (via trigger or application code)
Step 4: Query using @@ operator with ts_rank() for ordering
```

### Search API

```
GET /search?q=login+bug&type=task&project_id=uuid

Response:
{
  "results": [
    {
      "type": "task",
      "id": "...",
      "title": "Fix <b>login</b> <b>bug</b> on mobile",
      "rank": 0.85,
      "project": "Mobile App"
    }
  ],
  "total": 5
}
```

---

## Elasticsearch (When to Upgrade)

Consider Elasticsearch when you need:
- Fuzzy matching (typo tolerance)
- Faceted search (filter by category, count by status)
- Multi-language search
- Complex relevance tuning
- Search across millions of documents
- Auto-complete suggestions

For DevFlow, PostgreSQL FTS is sufficient until you have 100k+ searchable records.

---

## What I Should Be Able to Do Afterward

- [ ] Set up PostgreSQL full-text search with tsvector and GIN indexes
- [ ] Write search queries with ranking and highlighting
- [ ] Implement a search API endpoint
- [ ] Understand when to upgrade to Elasticsearch
- [ ] Index multiple fields with different weights
