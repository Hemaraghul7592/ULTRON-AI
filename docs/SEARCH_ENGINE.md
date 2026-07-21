# Search Engine — ULTRON AI

## Architecture

```
AI Engine → ToolExecutor → PluginManager → TavilyPlugin
                                                  │
                                           SearchService
                                           │         │
                                     SearchCache  TavilyProvider
                                                      │
                                                   Tavily API
```

All search flows through `SearchService`. The AI never calls a provider directly.

## Core Files

| File | Purpose |
|------|---------|
| `app/search/interface.py` | `SearchProvider` ABC + types (`SearchQuery`, `SearchResult`, `SearchResponse`, `ResearchQuery`, `ResearchResponse`, `Citation`, `SearchFeature`) |
| `app/search/cache.py` | `SearchCache` with configurable TTL, SHA-256 keyed, hit/miss tracking |
| `app/search/service.py` | `SearchService` — single entry point for all search |
| `app/search/providers/tavily.py` | `TavilyProvider` — wraps Tavily API behind `SearchProvider` |
| `app/plugins/tavily_plugin.py` | Updated to call `SearchService` (v3.0.0) |

## SearchProvider Interface

| Method | Returns | Description |
|--------|---------|-------------|
| `search(query)` | `SearchResponse` | Standard web search |
| `research(query)` | `ResearchResponse` | Deep research with answer + citations |
| `health_check()` | `dict` | Provider health status |
| `validate()` | `bool` | Credentials present |
| `metadata()` | `dict` | Provider name + features |
| `supported_features()` | `list[str]` | Feature flags |

## SearchService Methods

| Method | Description |
|--------|-------------|
| `search(query)` | Validate → cache check → provider call (with timeout) → deduplicate → cache set → return |
| `research(query)` | Same flow but for deep research with citations |
| `health_check()` | Provider health + cache stats |
| `clear_cache()` | Flush all cached entries |
| `cache_stats()` | Size, hits, misses, hit rate |
| `format_citations(results)` | Static: convert results to citation list with indices |

## SearchCache

- `SearchCache(default_ttl=300)` — 5 min default
- Uses SHA-256 of normalized query + params as key
- `get(query, **params)` — returns `None` on miss/expiry
- `set(query, data, ttl, **params)` — optional per-entry TTL
- `invalidate(query, **params)` — remove single entry
- `clear()` — flush all
- `stats()` — size, hits, misses, hit rate

To swap for Redis later: implement `SearchCache` with the same interface using Redis as backend.

## Response Format

### `SearchResponse`
```python
{
    "results": [SearchResult],
    "total_results": int,
    "query": str,
    "answer": None,
    "provider": str,
    "cached": bool,
    "mode": "standard",
}
```

### `ResearchResponse`
```python
{
    "answer": str,
    "results": [SearchResult],
    "citations": [Citation],
    "query": str,
    "provider": str,
    "cached": bool,
    "mode": "deep",
    "total_results": int,
}
```

### `SearchResult`
```python
{
    "title": str,
    "url": str,
    "source": str,          # Extracted domain
    "snippet": str,         # Content preview
    "published_date": str | None,
    "score": float,
}
```

### `Citation`
```python
{
    "title": str,
    "url": str,
    "source": str,
    "snippet": str,
    "published_date": str | None,
    "index": int,           # 1-based
}
```

## Search Modes

| Mode | Description |
|------|-------------|
| `standard` | `SearchService.search()` — quick web search, returns results list |
| `deep` | `SearchService.research()` — includes AI-generated answer + numbered citations |

The architecture supports adding new modes by extending `SearchProvider`.

## Error Handling

Errors are normalized into `SearchProviderError` subclasses:

| Error | When |
|-------|------|
| `SearchAuthError` | 401/403, missing API key |
| `SearchRateLimitError` | 429 |
| `SearchTimeoutError` | Request exceeded timeout |
| `SearchUnavailableError` | Provider unreachable |
| `SearchProviderError` | Generic provider error |

## TavilyProvider

Wraps the existing Tavily API with:
- Retry logic (2 attempts on 5xx)
- Timeout handling
- Error mapping (401 → SearchAuthError, 429 → SearchRateLimitError)
- Source extraction (strips `www.` from URLs)
- Domain filtering support

## AI Integration

The Tavily plugin's tools (`tavily_search`, `tavily_answer`) now call `SearchService` via `get_search_service()` instead of making direct HTTP calls. The AI flow is:

```
ChatService → ToolExecutor → PluginManager → TavilyPlugin → SearchService → TavilyProvider → Tavily API
```

## Testing

`tests/test_search.py` — 48 tests covering:
- SearchProvider interface (name, health, validate, metadata, features)
- SearchCache (miss, hit, expiry, normalization, invalidation, stats, TTL override)
- SearchService (search, research, dedup, caching, empty/long query, auth/rate-limit errors, timeout, health, clear cache)
- SearchService + SearchCache integration
- TavilyProvider (name, validate, health, search/research without key, features, source extraction)
- Citation formatting
- Deduplication across results and citations

## Future Extensibility

- Add new providers by implementing `SearchProvider` ABC (e.g., `GoogleSearchProvider`, `BingProvider`)
- Swap cache backend by implementing the same `get/set/clear/invalidate/stats` interface
- Add new research strategies by extending `SearchService` with more methods
- Register `SearchService` as a FastAPI dependency for REST search endpoints
