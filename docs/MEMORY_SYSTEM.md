# Memory Engine — ULTRON AI Platform

## Architecture

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────┐
│              Memory Engine                        │
│                                                   │
│  ┌──────────────┐    ┌───────────────────────┐    │
│  │  Incoming     │    │   Memory Classifier    │    │
│  │  Processor    │───►│  - Extract entities   │    │
│  │  - Embed text │    │  - Determine type     │    │
│  │  - Extract    │    │  - Score importance   │    │
│  │    keywords   │    │  - Tag extraction     │    │
│  └──────────────┘    └───────────┬───────────┘    │
│                                  │                │
│                                  ▼                │
│  ┌──────────────────────────────────────────┐     │
│  │         Memory Store                      │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐  │     │
│  │  │short_term│ │long_term │ │ semantic │  │     │
│  │  │ (volatile)│ │ (stable) │ │ (indexed) │  │     │
│  │  └──────────┘ └──────────┘ └──────────┘  │     │
│  └──────────────────────────────────────────┘     │
│                                                   │
│  ┌──────────────┐    ┌───────────────────────┐    │
│  │  Retrieval    │    │  Consolidation        │    │
│  │  - Semantic  │    │  - Summarize          │    │
│  │  - Keyword   │    │  - Merge duplicates   │    │
│  │  - Temporal  │    │  - Promote→long_term  │    │
│  │  - Ranked    │    │  - Expire old         │    │
│  └──────────────┘    └───────────────────────┘    │
└─────────────────────────────────────────────────┘
    │
    ▼
  Context Builder → AI Prompt
```

## Memory Types

| Type | Storage | TTL | Description |
|------|---------|-----|-------------|
| `short_term` | In-memory + DB | Session or 24h | Recent conversation context. Ephemeral. Automatically consolidated. |
| `long_term` | DB (indexed) | Indefinite | Important facts, preferences, learned patterns. Promoted from short-term. |
| `episodic` | DB (indexed) | Indefinite | Specific events, interactions, experiences. Timestamped. |
| `semantic` | DB (vector) | Indefinite | General knowledge, concepts, facts extracted from interactions. |
| `procedural` | DB | Indefinite | How-to knowledge, user preferences for task execution. |

## Memory Lifecycle

```
Creation → Short-Term ──→ Consolidation ──→ Long-Term
              │                                  │
              │ (expired/                         │ (accessed)
              │  low importance)                  │
              ▼                                  ▼
           Deleted                           Renewed (new TTL)
              │
              ▼
         Archived (optional)
```

## Memory Scoring (Importance)

Importance score (0.0 – 1.0) determines memory retention:

| Signal | Weight | Example |
|--------|--------|---------|
| Explicit user instruction | 0.35 | "Remember that my birthday is Jan 15." |
| Repetition | 0.25 | User mentions the same fact across sessions |
| Emotional content | 0.20 | "I really hate that." / "I love this." |
| Recency | 0.10 | Latest interactions score higher |
| Entity density | 0.10 | More named entities = more important |

Formula:
```
importance = Σ(signal_i × weight_i), clipped to [0.0, 1.0]
```

## Memory Retrieval

### Retrieval Strategies

```
┌─────────────────────┐
│   Query             │
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
Semantic     Keyword
Search       Search
(embeddings) (full-text)
    │           │
    └─────┬─────┘
          ▼
    ┌─────────────┐
    │  Fusion     │ ← Reciprocal Rank Fusion
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  Re-ranking │ ← Apply importance boost
    └──────┬──────┘
           ▼
    ┌─────────────┐
    │  Context    │ ← Trim to token budget
    │  Assembly   │
    └─────────────┘
```

### Context Budget

```
Total prompt tokens: 4096 (default)
Budget allocation:
  ├── System prompt:      500
  ├── Conversation:      2000
  ├── Memory context:    1000  ← memories compete for this
  ├── Tool results:       500
  └── Response reserve:    96
```

Memories are ranked by `importance × recency_decay` and included until the budget is exhausted.

## Consolidation Pipeline

Runs every 30 minutes (configurable) via background scheduler:

1. **Scan short-term memories** older than threshold
2. **Cluster similar** by embedding cosine similarity > 0.85
3. **Summarize clusters** into single long-term memory
4. **Check importance** — only promote if > 0.4
5. **Expire** short-term memories < 0.2 importance
6. **Update access count** on promoted memories

## Future: Vector Search

```
Embedding dimension: 384 (all-MiniLM-L6-v2)
Index type: IVFFlat (pgvector)
Distance: cosine

Query embedding → IVFFlat index → Approximate nearest neighbors → Re-rank
```

When switching to Qdrant:
- Dual-write to pgvector + Qdrant during migration
- Cutover when Qdrant is fully caught up
- pgvector becomes fallback read-only

## API Endpoints

See [API_SPECIFICATION.md](./API_SPECIFICATION.md#memory) for endpoint details.
