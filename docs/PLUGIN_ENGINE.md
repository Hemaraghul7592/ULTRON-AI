# Plugin Engine — ULTRON AI

## Architecture

```
AI Engine → ToolExecutor → PluginManager → PluginInterface → Plugin
                                                   │
                                           ┌───────┴───────┐
                                           │               │
                                      GitHub/Drive    Calendar/Gmail
                                      Tavily          (5 updated)
```

## Core Files

| File | Purpose |
|------|---------|
| `app/plugins/base.py` | `PluginInterface` ABC — extends `BasePlugin` with health, permissions, metadata |
| `app/plugins/errors.py` | `PluginError` hierarchy + `normalize_error()` + `error_response()` |
| `app/plugins/manager.py` | `PluginManager` — central entry point |
| `app/ai/tool_executor.py` | `ToolExecutor.sync_from_plugin_manager()` — wires AI to plugins |
| `app/plugins/*.py` | Individual plugin implementations |

## PluginInterface Methods

| Method | Description |
|--------|-------------|
| `name` | Plugin name (property) |
| `version` | Semver string (property) |
| `description` | Human-readable description (property) |
| `required_credentials` | List of required env vars (property, abstract) |
| `get_tools()` | List of `BaseTool` instances |
| `initialize(config)` | Startup hook |
| `cleanup()` | Shutdown hook |
| `health_check()` | Returns `PluginHealth` dict |
| `validate()` | Returns `True` if credentials present |
| `execute_tool(name, **kwargs)` | Execute a specific tool |
| `get_metadata()` | Plugin metadata dict |
| `get_permission_scope()` | Permission declarations |

## Plugin Statuses

| Status | Meaning |
|--------|---------|
| `loaded` | Module imported |
| `initialized` | `initialize()` called |
| `available` | Healthy and ready |
| `disabled` | User-disabled |
| `auth_failed` | Credentials missing/invalid |
| `rate_limited` | API rate-limited |
| `unavailable` | External API down |
| `error` | Unexpected error |

## PluginManager API

| Method | Description |
|--------|-------------|
| `initialize()` | Load all built-in plugins |
| `shutdown()` | Cleanup all plugins, clear state |
| `get_plugin(name)` | Get plugin by name |
| `get_all_plugins()` | Get all loaded plugins |
| `get_tool_definitions()` | OpenAI-compatible tool definitions |
| `get_all_tools()` | Tool list with plugin name |
| `get_status(name)` | Get plugin status |
| `set_status(name, status)` | Set plugin status |
| `get_all_statuses()` | Dict of all statuses |
| `health_check(name)` | Single plugin health |
| `health_check()` | All plugins health summary |
| `execute_tool(name, **kwargs)` | Execute (raises `PluginError`) |
| `execute_tool_safe(name, **kwargs)` | Execute (returns error dict) |
| `get_stats()` | Counts and per-plugin details |
| `get_plugin_metadata(name)` | Get cached metadata |
| `get_all_plugin_metadata()` | All cached metadata |

## API Endpoints

All under `/api/v1/tools`, requires Bearer auth.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tools` | List all tools |
| GET | `/tools/definitions` | OpenAI function definitions |
| POST | `/tools/execute` | Execute a tool |
| GET | `/tools/plugins` | Plugin stats |
| GET | `/tools/health` | Health check all plugins |
| GET | `/tools/health/{name}` | Health check single plugin |
| GET | `/tools/status` | All plugin statuses |

## Error Hierarchy

```
PluginError
├── PluginNotFoundError
├── PluginAuthError
├── PluginRateLimitError
├── PluginTimeoutError
├── PluginExecutionError
├── PluginUnavailableError
└── PluginConfigError
```

`normalize_error()` maps common HTTP errors to the correct type. `execute_tool_safe()` catches all and returns a dict with `success`, `error`, `error_type`, `plugin`, `tool`.

## Updated Plugins (v2.0.0)

| Plugin | Credentials | Tools |
|--------|------------|-------|
| GitHub | `GITHUB_TOKEN` | `github_list_repos`, `github_search`, `github_list_issues` |
| Google Drive | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `search_google_drive`, `read_google_drive_file` |
| Google Calendar | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `list_calendar_events`, `create_calendar_event` |
| Gmail | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | `search_gmail`, `read_gmail_message` |
| Tavily | `TAVILY_API_KEY` | `tavily_search`, `tavily_answer` |

Other plugins (weather, notion, ocr, google_maps, people) remain unchanged with `BasePlugin`.

## Tests

`tests/test_plugins.py` — 41 tests covering:
- PluginInterface (abstract credentials, metadata, permissions, health, validate, execute)
- PluginError hierarchy and normalization
- PluginManager (registration, query, health, execution, status, shutdown)
- ToolExecutor sync from PluginManager
- PluginStatus labels
