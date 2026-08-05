from __future__ import annotations

import json
import os
import subprocess
from typing import TYPE_CHECKING

from app.operations.incidents.domain.enums import EvidenceCategory
from app.operations.incidents.infrastructure.collectors.base import BaseCollector

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident, IncidentEvidence


class HealthSnapshotCollector(BaseCollector):
    name = "health_snapshot"
    category = EvidenceCategory.SYSTEM

    def __init__(self) -> None:
        self._snapshot: dict | None = None

    def set_snapshot(self, snapshot: dict) -> None:
        self._snapshot = snapshot

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if self._snapshot is None:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_snapshot",
                content="No health snapshot available",
            )
        content = json.dumps(self._snapshot, indent=2, default=str)
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="latest_snapshot",
            content=content,
        )


class MetricsSnapshotCollector(BaseCollector):
    name = "metrics_snapshot"
    category = EvidenceCategory.METRIC

    def __init__(self) -> None:
        self._metrics: dict = {}

    def set_metrics(self, metrics: dict) -> None:
        self._metrics = metrics

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._metrics:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_metrics",
                content="No metrics snapshot available",
            )
        content = json.dumps(self._metrics, indent=2, default=str)
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="latest_metrics",
            content=content,
        )


class GitCommitCollector(BaseCollector):
    name = "git_commit"
    category = EvidenceCategory.DEPLOYMENT

    def __init__(self, repo_path: str = ".") -> None:
        self._repo_path = repo_path

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self._repo_path,
                timeout=10,
            )
            commit_hash = result.stdout.strip()
            if result.returncode != 0 or not commit_hash:
                return self._safe_build(
                    incident,
                    source=self.name,
                    payload_ref="no_git",
                    content="Unable to determine git commit hash",
                )

            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self._repo_path,
                timeout=10,
            )
            branch = branch_result.stdout.strip()

            return self._safe_build(
                incident,
                source=self.name,
                payload_ref=commit_hash[:12],
                content=f"Commit: {commit_hash}\nBranch: {branch}",
                metadata={"commit_hash": commit_hash, "branch": branch},
            )
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="git_error",
                content=f"Git collection failed: {exc}",
            )


class GitDiffCollector(BaseCollector):
    name = "git_diff"
    category = EvidenceCategory.DEPLOYMENT

    def __init__(self, repo_path: str = ".") -> None:
        self._repo_path = repo_path

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                capture_output=True,
                text=True,
                cwd=self._repo_path,
                timeout=10,
            )
            recent_commits = result.stdout.strip()

            diff_result = subprocess.run(
                ["git", "diff", "HEAD~1", "--stat"],
                capture_output=True,
                text=True,
                cwd=self._repo_path,
                timeout=10,
            )
            diff_stat = diff_result.stdout.strip()

            content = f"Recent commits:\n{recent_commits}\n\nRecent diff:\n{diff_stat}"
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="recent_changes",
                content=content,
            )
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="git_diff_error",
                content=f"Git diff collection failed: {exc}",
            )


class EnvironmentVariableCollector(BaseCollector):
    name = "environment_variables"
    category = EvidenceCategory.CONFIG

    SENSITIVE_PATTERNS = [
        "key",
        "secret",
        "token",
        "password",
        "passwd",
        "auth",
        "credential",
        "api_key",
    ]

    REDACTED_PLACEHOLDER = "***REDACTED***"

    def __init__(self) -> None:
        self._keys_to_collect: list[str] | None = None

    def set_keys(self, keys: list[str]) -> None:
        self._keys_to_collect = keys

    async def collect(self, incident: Incident) -> IncidentEvidence:
        keys = self._keys_to_collect or list(os.environ.keys())
        env_data: dict[str, str] = {}

        for key in keys:
            if key not in os.environ:
                continue
            if self._is_sensitive(key):
                env_data[key] = self.REDACTED_PLACEHOLDER
            else:
                env_data[key] = os.environ[key]

        content = json.dumps(env_data, indent=2, default=str)
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="env_vars",
            content=content,
            metadata={"var_count": str(len(env_data))},
        )

    def _is_sensitive(self, key: str) -> bool:
        key_lower = key.lower()
        return any(pattern in key_lower for pattern in self.SENSITIVE_PATTERNS)


class ConfigCollector(BaseCollector):
    name = "configuration"
    category = EvidenceCategory.CONFIG

    REDACTED_KEYS = {
        "SECRET_KEY",
        "ENCRYPTION_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "GROK_API_KEY",
        "GITHUB_TOKEN",
        "TAVILY_API_KEY",
        "OPEN_WEATHER_API_KEY",
        "OCR_API_KEY",
        "NOTION_API_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REFRESH_TOKEN",
        "GOOGLE_MAPS_API_KEY",
    }

    def __init__(self) -> None:
        self._config: dict | None = None

    def set_config(self, config: dict) -> None:
        self._config = config

    async def collect(self, incident: Incident) -> IncidentEvidence:
        config = self._config or {}
        redacted: dict[str, str] = {}
        for key, value in config.items():
            if key in self.REDACTED_KEYS:
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = str(value)

        content = json.dumps(redacted, indent=2, default=str)
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="app_config",
            content=content,
        )


class StartupSequenceCollector(BaseCollector):
    name = "startup_sequence"
    category = EvidenceCategory.STATE

    def __init__(self) -> None:
        self._sequence: list[str] = []

    def record(self, step: str) -> None:
        self._sequence.append(step)

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._sequence:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_sequence",
                content="No startup sequence recorded",
            )
        content = "\n".join(f"[{i}] {step}" for i, step in enumerate(self._sequence))
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="startup_sequence",
            content=content,
            metadata={"steps": str(len(self._sequence))},
        )
