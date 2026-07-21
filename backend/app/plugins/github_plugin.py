from __future__ import annotations

from typing import Any

import httpx

from app.plugins.base import PluginInterface, PluginStatus
from app.tools.base import BaseTool


class GitHubRepoTool(BaseTool):
    def __init__(self, token: str) -> None:
        self._token = token
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "github_list_repos"

    @property
    def description(self) -> str:
        return "List GitHub repositories for the authenticated user"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "per_page": {"type": "integer", "default": 10},
                "sort": {
                    "type": "string",
                    "enum": ["updated", "created", "pushed"],
                    "default": "updated",
                },
            },
        }

    async def execute(self, **kwargs: Any) -> str:
        per_page = kwargs.get("per_page", 10)
        sort = kwargs.get("sort", "updated")

        if not self._token:
            return "GitHub token not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            resp = await self._client.get(
                "https://api.github.com/user/repos",
                headers={"Authorization": f"token {self._token}"},
                params={"per_page": per_page, "sort": sort},
            )
            resp.raise_for_status()
            repos = resp.json()
            if not repos:
                return "No repositories found"
            results = [f"Your repositories ({len(repos)}):"]
            for repo in repos:
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language", "N/A")
                results.append(
                    f"- {repo['name']}: {repo.get('description', 'No description')}"
                    f" [{lang}] Stars: {stars}",
                )
            return "\n".join(results)
        except Exception as e:
            return f"GitHub error: {e}"


class GitHubSearchTool(BaseTool):
    def __init__(self, token: str) -> None:
        self._token = token
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "github_search"

    @property
    def description(self) -> str:
        return "Search GitHub repositories"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "language": {"type": "string", "description": "Filter by language"},
                "sort": {
                    "type": "string",
                    "enum": ["stars", "forks", "updated"],
                    "default": "stars",
                },
                "per_page": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        language = kwargs.get("language", "")
        sort = kwargs.get("sort", "stars")
        per_page = kwargs.get("per_page", 10)

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            full_query = query
            if language:
                full_query += f" language:{language}"

            headers = {}
            if self._token:
                headers["Authorization"] = f"token {self._token}"

            resp = await self._client.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params={"q": full_query, "sort": sort, "per_page": per_page},
            )
            resp.raise_for_status()
            data = resp.json()
            repos = data.get("items", [])
            if not repos:
                return f"No repositories found for '{query}'"
            results = [f"Search results ({len(repos)} repos):"]
            for repo in repos:
                results.append(
                    f"- {repo['full_name']}: {repo.get('description', '')[:80]}"
                    f" Stars: {repo.get('stargazers_count', 0)}",
                )
            return "\n".join(results)
        except Exception as e:
            return f"GitHub search error: {e}"


class GitHubIssuesTool(BaseTool):
    def __init__(self, token: str) -> None:
        self._token = token
        self._client: httpx.AsyncClient | None = None

    @property
    def name(self) -> str:
        return "github_list_issues"

    @property
    def description(self) -> str:
        return "List issues in a GitHub repository"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                "per_page": {"type": "integer", "default": 10},
            },
            "required": ["owner", "repo"],
        }

    async def execute(self, **kwargs: Any) -> str:
        owner = kwargs.get("owner", "")
        repo = kwargs.get("repo", "")
        state = kwargs.get("state", "open")
        per_page = kwargs.get("per_page", 10)

        if not self._token:
            return "GitHub token not configured"

        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)

        try:
            resp = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                headers={"Authorization": f"token {self._token}"},
                params={"state": state, "per_page": per_page},
            )
            resp.raise_for_status()
            issues = resp.json()
            if not issues:
                return f"No {state} issues in {owner}/{repo}"
            results = [f"Issues in {owner}/{repo} ({len(issues)}):"]
            for issue in issues:
                labels = ", ".join(l["name"] for l in issue.get("labels", []))
                results.append(
                    f"#{issue['number']}: {issue['title']}" + (f" [{labels}]" if labels else ""),
                )
            return "\n".join(results)
        except Exception as e:
            return f"GitHub issues error: {e}"


class Plugin(PluginInterface):
    @property
    def name(self) -> str:
        return "github"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def description(self) -> str:
        return "GitHub repository and issue management"

    @property
    def required_credentials(self) -> list[str]:
        return ["GITHUB_TOKEN"]

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []
        self._token: str = ""

    def get_tools(self) -> list[BaseTool]:
        return self._tools

    async def initialize(self, config: dict | None = None) -> None:
        from app.core.config import get_settings

        settings = get_settings()
        self._token = settings.GITHUB_TOKEN
        if self._token:
            self._tools = [
                GitHubRepoTool(self._token),
                GitHubSearchTool(self._token),
                GitHubIssuesTool(self._token),
            ]

    async def health_check(self) -> dict:
        import time

        if not self._token:
            return {
                "status": PluginStatus.AUTH_FAILED,
                "message": "GITHUB_TOKEN not configured",
                "last_check": time.time(),
            }
        if not self._tools:
            return {
                "status": PluginStatus.DISABLED,
                "message": "No tools initialized",
                "last_check": time.time(),
            }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.github.com/",
                    headers={"Authorization": f"token {self._token}"},
                )
                if resp.status_code == 200:
                    return {
                        "status": PluginStatus.AVAILABLE,
                        "message": "GitHub API reachable",
                        "last_check": time.time(),
                    }
                return {
                    "status": PluginStatus.AUTH_FAILED,
                    "message": f"GitHub API returned {resp.status_code}",
                    "last_check": time.time(),
                }
        except Exception as e:
            return {
                "status": PluginStatus.UNAVAILABLE,
                "message": str(e),
                "last_check": time.time(),
            }

    async def validate(self) -> bool:
        return bool(self._token)

    async def cleanup(self) -> None:
        for tool in self._tools:
            if hasattr(tool, "close"):
                await tool.close()
