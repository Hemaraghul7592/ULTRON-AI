# Agent System — ULTRON AI

## Architecture

```
AgentService (single entry point)
        │
        ├── Planner
        │       Analyzes user request
        │       Determines intents via regex patterns
        │       Builds TaskGraph with dependencies
        │
        ├── TaskGraph
        │       Ordered tasks (DAG with deps)
        │       Status: pending → in_progress → completed/failed
        │       Priority-based execution ordering
        │
        ├── Executor
        │       Executes tasks respecting dependencies
        │       Retries transient failures
        │       Collects results into AgentContext
        │       Deadlock detection
        │
        ├── AgentContext
        │       Carries state across execution
        │       conversation_id, memory_refs, file_refs
        │       search_results, plugin_results, sync_state
        │       Execution log with timing
        │
        └── Service Handlers (registered at runtime)
                AI, Memory, Search, File, Plugin, Voice, Sync
```

## Core Files

| File | Purpose |
|------|---------|
| `app/agent/service.py` | `AgentService` — single entry point, registers handlers, orchestrates |
| `app/agent/planner.py` | `Planner` — intent detection via regex, builds `TaskGraph` |
| `app/agent/models.py` | `Task`, `TaskGraph` — DAG with dependencies, priority, retry |
| `app/agent/executor.py` | `Executor` — runs task graph, retries, timeout, deadlock detection |
| `app/agent/context.py` | `AgentContext` — state propagation across tasks + execution log |
| `app/agent/errors.py` | `AgentError` hierarchy (6 types) |

## AgentService API

| Method | Description |
|--------|-------------|
| `register_service(name, handler)` | Register a service handler (ai, search, memory, etc.) |
| `process(message, user_id, conversation_id, context)` | Full pipeline: plan → execute → summary |
| `health_check()` | Registered services list |

## Planner Intent Detection

| Intent | Trigger patterns |
|--------|-----------------|
| `search` | search for, find, what/who is, look up, research, explain, how to, when/where/why |
| `memory` | remember, save, store this, note that, recall, my profile/preference |
| `file` | file, document, pdf, image, photo, upload, download, ocr, extract text |
| `plugin` | github, repo, issue, calendar, event, email, gmail, drive, weather, notion, contact, map |
| `voice` | voice, audio, speak, talk, listen, transcribe, synthesize |
| `sync` | sync, synchronize, backup, restore |

## Task Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Auto-generated UUID |
| `name` | str | Human-readable name |
| `service` | str | Service name (ai, search, memory, etc.) |
| `action` | str | Sub-action |
| `args` | dict | Arguments for the handler |
| `priority` | int | Lower = later in queue (0 default, 10 for AI) |
| `max_retries` | int | Retry count per task (default 2) |
| `depends_on` | list[str] | Task IDs this depends on |
| `status` | str | pending / in_progress / completed / failed |
| `result` | Any | Handler return value |
| `error` | str | Failure message |
| `attempts` | int | Execution attempt count |

## Execution Flow

```
1. Planner.plan() → TaskGraph
2. Executor.execute(graph, context):
   a. Find ready tasks (all deps satisfied)
   b. Sort by (-priority, insertion_order)
   c. For each ready task:
      - Set status → "in_progress"
      - Call registered handler(task, context)
      - On success: status → "completed"
      - On failure: retry if attempts < max_retries
      - On timeout: status → "failed"
   d. Add to completed_ids (completed OR failed)
   e. Repeat until graph is_complete()
3. Deadlock: if no ready tasks but pending ones exist → DependencyError
```

## Context Propagation

`AgentContext` is passed to every handler:

```python
async def handler(task: Task, context: AgentContext) -> str:
    context.memory_refs.append("mem_1")  # share state
    return "done"
```

Results flow: task → handler return value → context.execution_log → final summary.

## Error Hierarchy

```
AgentError
├── PlanningError
├── ExecutionError (carries task_id)
├── DependencyError   (deadlock)
├── TimeoutError
├── RecoveryError
```

## Test Summary

`tests/test_agent.py` — 45 tests covering:
- Task (create, to_dict, is_ready, can_retry)
- TaskGraph (add, get_ready, ordering, completion, failed, retry, to_dict)
- AgentContext (create, log, summary, to_dict, propagation)
- Planner (search, deep research, memory, plugin, file, multi-intent, AI deps)
- Executor (single task, sequential, retry, failure, no handler, timeout, context, logging, recovery, deadlock)
- AgentService (full pipeline, memory intent, health, failed tasks, context)
- Error hierarchy
- Full integration test
