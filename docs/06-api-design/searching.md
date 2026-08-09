# Searching

## 1. What Is It?

Search allows users to find resources by matching text against content fields. It goes beyond simple filtering — searching for "login bug" should find tasks with "login issue" or "authentication bug" in their title or description.

---

## 2. Why Does It Matter?

As DevFlow grows to hundreds or thousands of tasks, users need to find specific items quickly. Filtering by status or assignee isn't enough when you remember a keyword but not the exact task.

---

## 5. How Does It Work?

### Progressive Search Implementation

**Stage 1: ILIKE (Simple)**
```sql
WHERE title ILIKE '%query%' OR description ILIKE '%query%'
```
- Pros: Simple, no setup
- Cons: No ranking, no stemming, slow on large tables (no index support)

**Stage 2: PostgreSQL Full-Text Search (Recommended)**
```sql
WHERE search_vector @@ plainto_tsquery('english', 'query')
ORDER BY ts_rank(search_vector, plainto_tsquery('english', 'query')) DESC
```
- Pros: Ranking, stemming, GIN index support, highlighting
- Cons: More setup, language-dependent

**Stage 3: Elasticsearch (Advanced)**
- Pros: Fuzzy matching, faceted search, auto-complete, multi-language
- Cons: Additional infrastructure, data sync complexity

### DevFlow Search Approach

Start with PostgreSQL FTS (Stage 2). It handles most use cases without additional infrastructure. Consider Elasticsearch when you need fuzzy matching or faceted search at scale.

---

## What I Should Be Able to Do Afterward

- [ ] Implement text search with PostgreSQL full-text search
- [ ] Create GIN indexes on search vector columns
- [ ] Rank search results by relevance
- [ ] Highlight matching terms in results
- [ ] Combine search with filters and pagination
