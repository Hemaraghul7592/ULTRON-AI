# ADR-0001: Brain-Centric Architecture

## Status

Accepted — 2026-07-22

## Context

ULTRON consists of multiple engines: AI, Memory, Search, File, Voice, Sync,
Plugin, Agent, Identity, Personality, Goals, Relationship, Knowledge, Learning,
Observation, and Proactive. Each engine manages its own domain.

Without a central coordinator, engines operate in isolation. The AI Engine
doesn't know what the Memory Engine remembers. The Voice Engine doesn't
leverage the Observation Engine's context. The user gets disconnected,
single-domain responses rather than a cohesive companion experience.

A central coordinating component is needed — one that observes sensor input,
builds context from multiple engines, decides what action to take, selects
the appropriate AI model, and coordinates skill execution. This component
must not replace the engines but integrate them.

## Decision

ULTRON will use a **Brain-Centric Architecture** where a `Brain` module
serves as the central orchestrator.

The Brain:
- Receives all input (user messages, voice, sensor events, system triggers)
- Coordinates engine queries (memory, knowledge, goals, observation)
- Routes decisions through a `DecisionEngine` and `ThoughtPipeline`
- Delegates execution to Skills, AI models, and Computer Control
- Maintains a `ConsciousLoop` for continuous observe→think→act cycling
- Never duplicates engine functionality — it delegates and integrates

Engine communication flows exclusively through the Brain:

```
User Input → Brain → [Memory, Context, Goals, ...] → ThoughtPipeline → AI → Response
```

## Consequences

### Positive
- Single coordination point makes the system comprehensible and debuggable
- Engines remain independently testable with mock Brain contexts
- Adding a new engine requires only registering it with the Brain (no cross-engine wiring)
- AI model switching is transparent — the Brain selects the model, not the user
- The Conscious Loop enables proactive behavior (future milestone)

### Negative
- The Brain becomes a critical path — if it fails, the entire system degrades
- Over-abstracting the Brain could hide performance issues in engine queries
- The team must resist the temptation to put engine logic directly in the Brain

### Mitigations
- Brain implementation uses strict delegation — no engine logic in Brain code
- All Brain→Engine communication goes through defined protocols
- The Conscious Loop has configurable cadences to prevent CPU waste
- Health checks and circuit breakers protect against engine failures

## Alternatives Considered

### Event Bus / Pub-Sub Architecture
Engines communicate via events. An AI response publishes an event; Memory
listens and stores relevant context. **Rejected**: Too distributed — hard
to trace a user request through the system, difficult to debug ordering issues,
adds complexity without clear benefit at this scale.

### Direct Engine-to-Engine Wiring
Memory calls AI, AI calls Search, Search calls Voice. **Rejected**: Creates
tight coupling, makes AI model switching complex, requires every engine to
know about every other engine.

### Monolithic Engine
All functionality in one module. **Rejected**: Unmaintainable at scale,
hard to test, prevents independent engine evolution.

## References

- [ULTRON Architecture Document](./architecture.md)
- Phase 2 Backend: All 8 backend engines follow a single-entry-point pattern
  that the Brain extends into the macOS client.
