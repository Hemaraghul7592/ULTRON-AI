# Plugin Engine — ULTRON AI Platform

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Plugin Engine                        │
│                                                      │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │  Registry  │  │  Loader    │  │  Executor    │   │
│  │  - Built-in│  │  - Dynamic │  │  - Sandbox   │   │
│  │  - User    │  │  - Verify  │  │  - Timeout   │   │
│  │  - System  │  │  - Version │  │  - Rate limit│   │
│  └────────────┘  └────────────┘  └──────────────┘   │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │           Plugin Manifest                     │    │
│  │  name, version, author, permissions, hooks   │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Plugin Manifest Schema

```json
{
  "name": "github",
  "version": "1.0.0",
  "author": "ULTRON",
  "description": "GitHub repository management",
  "icon": "github-icon",
  "permissions": ["http:github.com", "user:read"],
  "tools": [
    {
      "name": "search_repos",
      "description": "Search GitHub repositories",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {"type": "string"},
          "limit": {"type": "integer", "default": 5}
        }
      }
    }
  ],
  "hooks": {
    "on_install": "setup_oauth",
    "on_uninstall": "revoke_oauth",
    "on_sync": "sync_data"
  },
  "oauth_scopes": ["repo", "user"],
  "config_schema": {
    "type": "object",
    "properties": {
      "github_token": {"type": "string", "format": "password"}
    }
  }
}
```

## Plugin Categories

| Category | Example | Auto-installed |
|----------|---------|----------------|
| **Built-in** | Weather, Search, Calculator | Yes |
| **First-party** | GitHub, Google Drive, Gmail, Calendar | On OAuth connect |
| **Community** | Third-party plugins | Marketplace install |
| **User** | Custom user scripts | Manual |

## Plugin Lifecycle

```
Discovered ──► Verified ──► Installed ──► Configured ──► Active
                  │                            │
                  ▼                            ▼
              Rejected                    Disabled / Uninstalled
```

## Execution Sandbox

```python
class PluginSandbox:
    """Security sandbox for plugin execution."""

    MAX_EXECUTION_TIME = 30  # seconds
    MAX_MEMORY_MB = 100
    ALLOWED_DOMAINS: set[str]  # from permissions
    RATE_LIMIT = "10/minute"
```

## Marketplace API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/plugins/marketplace` | List available plugins |
| GET | `/plugins/marketplace/{name}` | Plugin details |
| POST | `/plugins/install` | Install from marketplace |
| POST | `/plugins/{name}/uninstall` | Remove plugin |
| POST | `/plugins/{name}/configure` | Update config |
| GET | `/plugins/{name}/status` | Check status |

## Dynamic UI

Plugins define their UI via JSON Schema. Clients render native forms:

```json
{
  "settings_ui": {
    "type": "form",
    "fields": [
      {"key": "github_token", "type": "password", "label": "Personal Access Token"},
      {"key": "default_repo", "type": "text", "label": "Default Repository"}
    ]
  }
}
```

## Current Plugins (Phase 1)

All existing plugins (`weather`, `tavily`, `google_drive`, `gmail`, `calendar`, `github`, `notion`, `google_maps`, `people`, `ocr`) continue to work. Phase 2 adds:

- Dynamic loading from `plugins/` directory
- Plugin marketplace API
- Per-user enable/disable
- Configuration UI
- Permission scoping
