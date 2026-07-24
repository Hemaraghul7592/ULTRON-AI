# PR #2 — Dependency Injection Foundation

## Status: FROZEN ✅

No further architectural modifications should be made unless a bug or new product requirement is discovered.

---

## Architecture Overview

ULTRON's DI system follows a **container-based constructor injection** model with `@MainActor` confinement. All services declare dependencies in initializers. The container constructs the object graph lazily at resolution time. Circular dependencies are detected with a stack-based algorithm that preserves the full resolution chain for diagnostics.

**Single Source of Truth**: `_resolveCore(for:)` is the one canonical resolution pipeline. Every other code path — production `_resolve`, `_resolveIfRegistered`, validation `_validateRecord`, and dependency resolution via `ContainerResolver` — ultimately calls `_resolveCore`.

## Public API

```swift
// Registration
container.register(Type.self, lifetime: .singleton) { resolver in ... }
container.register(Type.self, lifetime: .transient) { resolver in ... }

// Diagnostics (read-only)
ContainerDiagnostics(container: container)
diag.validate()                         // Verify all singletons can start
diag.registeredTypes()                  // → [RegistrationSnapshot]
diag.dependencyGraph()                  // → [(service, dependencies)]
diag.totalRegistrations()              // → RegistrationStatistics

// Container metadata
container.registrationCount             // Active registrations
container.totalRegistrations            // Including overwrites
container.snapshot()                    // → [RegistrationSnapshot]

// Error types
ContainerError.notRegistered(type:)
ContainerError.circularDependency(chain:)
ContainerError.factoryFailed(type:underlying:)
```

## Source Files (11)

| File | Lines | Responsibility |
|------|-------|---------------|
| `DependencyContainer.swift` | 336 | Registration, resolution, cycle detection, diagnostics support |
| `ContainerDiagnostics.swift` | 143 | validate, registeredTypes, dependencyGraph, statistics |
| `ContainerError.swift` | 52 | Error enum with human-readable descriptions |
| `ContainerResolver.swift` | 36 | Thin Resolver → Container delegation bridge |
| `Resolver.swift` | 22 | Protocol: resolve, resolveIfRegistered |
| `ServiceLifetime.swift` | 26 | Enum: singleton, transient, reserved scoped |
| `ServiceRegistration.swift` | 42 | Immutable registration config |
| `ServiceRecord.swift` | 43 | Runtime storage: registration + index + cache |
| `RegistrationSnapshot.swift` | 51 | Public type metadata (hides internals) |
| `RegistrationStatistics.swift` | 25 | Active/total/overwritten counts |
| `ResolutionFrame.swift` | 30 | Structured stack frame for cycle detection |
| **Total** | **806** | |

## Test Files (2)

| File | Lines | Tests |
|------|-------|-------|
| `DependencyContainerTests.swift` | 881 | 54 tests: registration, resolution, cycle detection |
| `ContainerDiagnosticsTests.swift` | 403 | 28 tests: validate, types, graph, stats |
| **Total** | **1,284** | **82 tests** |

## Design Decisions

1. **`@MainActor` class, not actor** — Supports non-Sendable services (WindowManager, ThemeManager). Factory closures don't need `@Sendable`. Matches real startup flow (main thread).

2. **Zero `@unchecked Sendable`** — All concurrency safety is structural, not suppressed.

3. **Constructor injection only** — No property injection. No service locator. Every dependency is explicit.

4. **`RegistrationSnapshot` hides internals** — Public diagnostics never expose factory closures or cached instances.

5. **`ResolutionFrame` future-proofs the stack** — Adding timing/lifetime metadata requires one field, zero stack changes.

6. **Validation uses production pipeline** — `validate()` exercises the same `_resolveCore` as runtime resolution. Cycle detection, dependency resolution, and singleton caching are all active.

7. **Deterministic diagnostics** — All output sorted by registration index. Same results every run.

8. **No third-party dependencies** — Pure Swift. Foundation only.

## Known Limitations

1. No scoped lifetime — reserved for future milestone. Public API won't change when added.
2. No `reset()` for testing — singleton cache persists. Deliberate trade-off: production correctness over test convenience.
3. `dependencyGraph()` executes factories in observation mode — safe for side-effect-free factories. Documented contract.

## Future Extension Points

- `ServiceLifetime.scoped` — add a case, implement scope lifecycle. Zero API changes.
- `ResolutionFrame` — add `startTime`, `lifetime`, `registrationIndex` fields.
- `reset()` — add method that clears `records`, `nextIndex`, `resolutionStack`. Testing only.
- `ContainerDiagnostics` — add profiling, JSON export, GraphViz output.
- Assembly grouping — register related services together.

## Freeze Checklist

| Check | Status |
|-------|--------|
| No TODO | ✅ |
| No FIXME | ✅ |
| No debug code | ✅ |
| No commented-out code | ✅ |
| No duplicate logic | ✅ |
| No dead code | ✅ |
| No force unwrap | ✅ |
| No force cast | ✅ |
| No `@unchecked Sendable` | ✅ |
| No `fatalError` | ✅ |
| No retain cycle risks | ✅ |
| Public APIs documented | ✅ |
| MARK sections consistent | ✅ |
| File organization consistent | ✅ |
| Swift 6 concurrency satisfied | ✅ |
| One canonical resolution pipeline | ✅ |
| No architecture violations | ✅ |
