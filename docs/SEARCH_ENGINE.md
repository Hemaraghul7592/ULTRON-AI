# Search Engine — ULTRON AI Platform

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  Query Processor             │
│  - Expand / rewrite query   │
│  - Classify intent          │
│  - Detect research mode     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│     Cache Lookup             │
│  ┌─────────┐                │
│  │  Redis  │── hit ──► return cached │
│  └─────────┘                │
│       │ miss                │
│       ▼                     │
│  ┌──────────────────┐      │
│  │  Tavily API      │      │
│  └──────────────────┘      │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Result Processor            │
│  - Extract citations        │
│  - Rank by relevance        │
│  - Format for LLM context   │
│  - Store in history         │
└─────────────────────────────┘
```

## Search Modes

### Quick Search
- Single Tavily API call
- Returns top 5–10 results
- Cached for 1 hour
- Use case: General questions, quick facts

### Deep Research
- Multi-step search pipeline
- Query decomposition → parallel sub-searches → aggregation
- Results ranked by source authority + relevance
- Returns structured report with citations
- Use case: Complex topics, competitive analysis

### Streaming Research (future)
- Real-time WebSocket updates as each sub-search completes
- User sees intermediate results
- Can refine query mid-search

## Cache Strategy

```python
CACHE_TTL = {
    "quick": 3600,        # 1 hour
    "deep": 86400,        # 24 hours
    "research": 604800,   # 7 days
}

def get_cache_key(query: str, mode: str, user_id: str) -> str:
    return f"search:{user_id}:{mode}:{hash(query)}"
```

Cache is invalidated when:
- Explicit user request
- Source is known to have updated (future: webhook)

## Source Citations

```json
{
  "results": [
    {
      "title": "Latest AI Developments 2026",
      "url": "https://example.com/ai-2026",
      "snippet": "The field of artificial intelligence has seen remarkable progress...",
      "relevance_score": 0.95,
      "source_authority": 0.85,
      "published_date": "2026-06-15",
      "cached": true
    }
  ],
  "total_results": 42,
  "mode": "quick",
  "cache_hit": false,
  "latency_ms": 1234
}
```

## LLM Context Format

When search results are fed to AI:

```
<search_results>
[1] Title: Latest AI Developments 2026
    URL: https://example.com/ai-2026
    Content: The field of artificial intelligence has seen remarkable progress...

[2] Title: AI Regulation Update
    URL: https://example.com/ai-regulation
    Content: New regulations for AI systems were proposed today...
</search_results>

Based on the search results above, answer the user's question.
Cite sources using [1], [2] notation.
```

## Search History

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| query | TEXT | Original query |
| mode | VARCHAR | quick / deep / research |
| result_count | INT | Number of results |
| tokens_used | INT | Tokens consumed |
| cached | BOOLEAN | Was result cached? |
| created_at | TIMESTAMPTZ | Search timestamp |

History is retained for 90 days. Users can delete individual entries or clear all.
