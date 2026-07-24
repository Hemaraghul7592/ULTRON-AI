# ULTRON macOS

Personal AI Operating Companion for macOS.

## Requirements

- macOS 14 (Sonoma) or later
- Xcode 16 or later (Swift 6.0)
- Command Line Tools alone are insufficient — Xcode is required for SwiftPM manifest compilation

## Architecture Overview

ULTRON follows a **Brain-Centric Architecture** where a central `Brain` module
orchestrates all engines. Each engine manages its own domain (Memory, Voice,
Search, Files, etc.) and communicates exclusively through the Brain.

For details, see [ADR-0001](docs/architecture/adr/0001-brain-centric-architecture.md).

## Quick Start

```bash
# 1. Ensure Xcode is selected
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# 2. Open the project
open Package.swift

# 3. Build
swift build

# 4. Run tests
swift test

# 5. Build for release
swift build -c release
```

## Project Structure

```
macos/
├── Package.swift                    # SPM manifest (Swift 6.0, macOS 14+)
├── Configuration/                   # Build configurations
│   ├── Development.xcconfig
│   ├── Debug.xcconfig
│   ├── Release.xcconfig
│   └── Production.xcconfig
├── Sources/ULTRON/                  # Executable target
│   ├── ULTRONApp.swift              # @main entry point
│   ├── AppDelegate.swift            # NSApplicationDelegate lifecycle
│   └── Core/
│       ├── Configuration/           # Build + runtime configuration
│       └── Lifecycle/               # Startup/shutdown sequencing
├── Tests/UnitTests/                 # Unit test target
├── docs/                            # Project documentation
│   ├── architecture/
│   │   └── adr/                     # Architecture Decision Records
│   └── README.md
└── README.md
```

## Build Configurations

| Configuration | Compiler Flags | Optimization | Purpose |
|--------------|---------------|-------------|---------|
| Development | `-D DEVELOPMENT` | `-Onone` | Day-to-day engineering |
| Debug | `-D DEBUG` | `-Onone` | Internal QA testing |
| Release | `-D RELEASE` | `-O` | Beta distribution |
| Production | `-D PRODUCTION` | `-Osize` | App Store / direct distribution |

## Startup Sequence

The application initializes in clearly defined phases. Each phase is a
case in the `StartupPhase` enum. Hooks declare which phase they belong to,
and the system executes phases in declaration order with zero magic numbers.

```
case configuration       →  Environment, build flags, runtime config
case logging             →  Structured logging, OSLog
case dependencyInjection →  Dependency container, assembly
case applicationState    →  App state, lifecycle state
case windowSystem        →  Window manager, menu bar, overlay
case ready               →  Final initialization, services
```

Within each phase, hooks with lower `priority` values execute first.
Adding a new phase requires only adding a new case to `StartupPhase` —
zero changes to `StartupSequence` or `ShutdownSequence`.

## Development Workflow

### Branch Strategy

- `main` — Production-ready code. Protected. Requires PR + review.
- `develop` — Integration branch. All feature PRs target this.
- `feature/*` — Individual feature branches. Short-lived.
- `fix/*` — Bug fix branches. Target `develop` or `main` (hotfix).

### Pull Request Workflow

1. Create a feature branch from `develop`
2. Implement changes following the coding standards below
3. Write tests covering new behavior
4. Run `swift test` and `swift build`
5. Create a PR against `develop`
6. At least one review required before merge
7. Squash merge to keep history clean

### Commit Conventions

```
type(scope): description

Types: feat, fix, refactor, test, docs, chore
Scope: module name (e.g., lifecycle, config, app)
```

## Coding Standards

- Swift 6 with strict concurrency checking
- `@MainActor` for all UI-related types
- Actors for shared mutable state
- Structs by default; classes only when reference semantics required
- Protocols for all abstractions
- No force unwrapping (`!`) in production code
- No `@unchecked Sendable` — use proper actor isolation instead
- Maximum line length: 140 characters
- Maximum function body: 60 lines (soft limit)
- All public types and methods must have documentation comments
- Use `// MARK: -` to organize code sections

## Testing Strategy

### Test Pyramid

```
    ┌──────┐
    │  UI  │  10% — XCUITest (future milestone)
    ├──────┤
    │ Int. │  20% — Multiple modules working together (future milestone)
    ├──────┤
    │ Unit │  70% — Individual types in isolation (current milestone)
    └──────┘
```

### Running Tests

```bash
swift test                          # All tests
swift test --filter Configuration   # Specific suite
```

### Test Conventions

- Use Swift Testing (`import Testing`) for new tests
- Test file names: `<Module>Tests.swift`
- One test file per module
- Use `#expect` for assertions
- Mock dependencies with protocol-based test doubles
- Test edge cases: empty state, duplicates, failures, ordering

## Known Issues

### Command Line Tools on macOS 14+

SwiftPM manifest compilation fails with Command Line Tools alone due to
a linker issue with the `PackageDescription` library. This is fixed by
installing Xcode. Verify with:

```bash
xcode-select -p
# Must show: /Applications/Xcode.app/Contents/Developer
```

## Documentation

- [Architecture Decision Records](docs/architecture/adr/)
- [ULTRON Architecture](../../docs/) (project root)
