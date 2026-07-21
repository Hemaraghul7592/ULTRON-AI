# Coding Standards — ULTRON AI Platform

## Language-Specific Conventions

### Python (Backend)

```
Format:    Ruff (line length: 120)
Types:     Strict mypy, no `Any` unless unavoidable
Imports:   standard → third-party → first-party (groups separated)
Logging:   structlog, never print()
Async:     All I/O is async. Avoid asyncio.run() in production.
Models:    SQLAlchemy 2.0 Mapped annotation style
Schemas:   Pydantic v2, use model_validator for cross-field validation
Tests:     pytest + pytest-asyncio, conftest.py for fixtures
```

### Kotlin (Android)

```
Format:    ktlint (standard rules)
Null safety: Explicit nulls, no !!
Imports:   Explicit, no wildcard imports
State:     StateFlow / MutableStateFlow, no LiveData in new code
DI:        Hilt @Inject constructor, no field injection
Layout:    Jetpack Compose, no XML layouts
Navigation: Navigation Compose, type-safe routes (future)
Room:      Entities mirror API DTOs with sync metadata
```

### Swift (iOS — Phase 2)

```
Format:    swift-format
Null safety: Optional chaining, guard let early return
State:     @Observable / @Published, Combine for reactive
UI:        SwiftUI, no UIKit in new code
Network:   Async/await URLSession, generated from OpenAPI
Storage:   SwiftData or CoreData
DI:        Factory pattern or Swinject
```

## Naming Conventions

| Concept | Python | Kotlin | Swift |
|---------|--------|--------|-------|
| API route | `snake_case` | `camelCase` | `camelCase` |
| Database | `snake_case` | `snake_case` (Room) | `snake_case` |
| Function/method | `snake_case` | `camelCase` | `camelCase` |
| Class | `PascalCase` | `PascalCase` | `PascalCase` |
| Variable | `snake_case` | `camelCase` | `camelCase` |
| Constant | `SCREAMING_SNAKE` | `SCREAMING_SNAKE` / `camelCase` | `camelCase` |
| Enum | `PascalCase` | `PascalCase` | `PascalCase` |
| File name | `snake_case.py` | `PascalCase.kt` | `PascalCase.swift` |

## Commit Convention

```
type(scope): description

Types: feat, fix, refactor, test, docs, chore, perf

Examples:
  feat(ai): add Gemini streaming support
  fix(chat): handle empty response from provider
  docs(api): update chat endpoint schema
  refactor(memory): extract embedding service
```

## Code Review Checklist

- [ ] No hardcoded secrets, URLs, or environment-specific values
- [ ] Error paths are handled (no bare `except`, no `!!`)
- [ ] Logging at appropriate level (info for state changes, debug for details)
- [ ] No unused imports, variables, or dead code
- [ ] Async methods use proper cancellation (CancellationToken / coroutine scope)
- [ ] Database queries are indexed (check EXPLAIN ANALYZE in review)
- [ ] API changes are reflected in OpenAPI spec
- [ ] Tests pass (existing + new)
- [ ] Migration scripts are reversible
- [ ] Client SDK is regenerated if API changes

## Testing Requirements

| Layer | Tool | Coverage Target |
|-------|------|-----------------|
| Backend unit | pytest | 90%+ |
| Backend integration | pytest + httpx | 80%+ |
| Backend API | pytest + TestClient | All endpoints |
| Android unit | JUnit + MockK | 80%+ |
| Android integration | Compose UI tests | Critical flows |
| iOS unit | XCTest | 80%+ |

## Documentation

- Every public API endpoint has OpenAPI documentation
- Every Python function has a docstring (Google style)
- Every Kotlin public function has KDoc
- Architecture decisions documented in `docs/`
- CHANGELOG.md updated per release
