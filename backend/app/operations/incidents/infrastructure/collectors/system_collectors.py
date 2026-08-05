from __future__ import annotations

from typing import TYPE_CHECKING

from app.operations.incidents.domain.enums import EvidenceCategory
from app.operations.incidents.infrastructure.collectors.base import BaseCollector

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import Incident, IncidentEvidence


class DockerStatusCollector(BaseCollector):
    name = "docker_status"
    category = EvidenceCategory.SYSTEM

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import docker

            client = docker.from_env()
            info = client.info()
            containers = client.containers.list(all=True)

            content_parts: list[str] = [
                f"Server Version: {info.get('ServerVersion', 'unknown')}",
                f"Containers: {info.get('Containers', 'unknown')}",
                f"Running: {info.get('ContainersRunning', 'unknown')}",
                f"Paused: {info.get('ContainersPaused', 'unknown')}",
                f"Stopped: {info.get('ContainersStopped', 'unknown')}",
            ]

            container_list = []
            for c in containers[:20]:
                try:
                    container_list.append(
                        f"  - {c.name}: {c.status} ({c.attrs.get('State', {}).get('Health', {}).get('Status', 'n/a')})"
                    )
                except Exception:
                    container_list.append(f"  - {c.name}: unknown")

            if container_list:
                content_parts.append("Containers:")
                content_parts.extend(container_list)

            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="docker_info",
                content="\n".join(content_parts),
            )
        except ImportError:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="sdk_missing",
                content="Docker SDK not installed",
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="docker_error",
                content=f"Docker status collection failed: {exc}",
            )


class RedisStatusCollector(BaseCollector):
    name = "redis_status"
    category = EvidenceCategory.SYSTEM

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or __import__("os").environ.get("REDIS_URL")

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._redis_url:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="not_configured",
                content="Redis URL not configured",
            )
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(self._redis_url, socket_connect_timeout=3)
            info = await client.info()
            await client.aclose()

            content_parts = [
                f"Redis Version: {info.get('redis_version', 'unknown')}",
                f"Connected Clients: {info.get('connected_clients', 'unknown')}",
                f"Used Memory: {info.get('used_memory_human', 'unknown')}",
                f"Used Memory Peak: {info.get('used_memory_peak_human', 'unknown')}",
                f"Total Connections Received: {info.get('total_connections_received', 'unknown')}",
                f"Total Commands Processed: {info.get('total_commands_processed', 'unknown')}",
                f"Keyspace Hits: {info.get('keyspace_hits', 'unknown')}",
                f"Keyspace Misses: {info.get('keyspace_misses', 'unknown')}",
            ]
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="redis_info",
                content="\n".join(content_parts),
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="redis_error",
                content=f"Redis status collection failed: {exc}",
            )


class DatabaseStatusCollector(BaseCollector):
    name = "database_status"
    category = EvidenceCategory.SYSTEM

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            from app.core.config import get_settings
            from app.core.database import get_engine

            settings = get_settings()
            engine = get_engine()
            if engine is None:
                return self._safe_build(
                    incident,
                    source=self.name,
                    payload_ref="not_initialized",
                    content="Database engine not initialized",
                )

            from sqlalchemy import text

            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()[0] if result else "unknown"

            db_url = settings.DATABASE_URL.split("@")[0] if "@" in settings.DATABASE_URL else "configured"
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="db_status",
                content=f"Database: {db_url}\nVersion: {version}",
                metadata={"url_redacted": "true"},
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="db_error",
                content=f"Database status collection failed: {exc}",
            )


class CpuStatusCollector(BaseCollector):
    name = "cpu_status"
    category = EvidenceCategory.METRIC

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1.0)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)
            load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0.0, 0.0, 0.0)

            content_parts = [
                f"CPU Percent: {cpu_percent}%",
                f"CPU Count (Logical): {cpu_count_logical}",
                f"CPU Count (Physical): {cpu_count_physical}",
                f"Load Average (1/5/15 min): {load_avg[0]:.2f}/{load_avg[1]:.2f}/{load_avg[2]:.2f}",
            ]
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="cpu_info",
                content="\n".join(content_parts),
            )
        except ImportError:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="psutil_missing",
                content="psutil not installed",
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="cpu_error",
                content=f"CPU status collection failed: {exc}",
            )


class MemoryStatusCollector(BaseCollector):
    name = "memory_status"
    category = EvidenceCategory.METRIC

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import psutil

            vm = psutil.virtual_memory()
            swap = psutil.swap_memory()

            content_parts = [
                f"Memory Total: {vm.total}",
                f"Memory Available: {vm.available}",
                f"Memory Used: {vm.used}",
                f"Memory Percent: {vm.percent}%",
                f"Swap Total: {swap.total}",
                f"Swap Used: {swap.used}",
                f"Swap Percent: {swap.percent}%",
            ]
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="memory_info",
                content="\n".join(content_parts),
            )
        except ImportError:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="psutil_missing",
                content="psutil not installed",
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="memory_error",
                content=f"Memory status collection failed: {exc}",
            )


class DiskStatusCollector(BaseCollector):
    name = "disk_status"
    category = EvidenceCategory.METRIC

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import shutil

            usage = shutil.disk_usage("/")
            content_parts = [
                f"Disk Total: {usage.total}",
                f"Disk Used: {usage.used}",
                f"Disk Free: {usage.free}",
                f"Disk Usage Percent: {(usage.used / usage.total) * 100:.1f}%",
            ]

            try:
                import psutil

                partitions = psutil.disk_partitions()
                for p in partitions[:10]:
                    try:
                        u = psutil.disk_usage(p.mountpoint)
                        content_parts.append(
                            f"  Mount {p.mountpoint}: {u.used / u.total * 100:.1f}% used"
                        )
                    except OSError:
                        pass
            except (ImportError, OSError):
                pass

            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="disk_info",
                content="\n".join(content_parts),
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="disk_error",
                content=f"Disk status collection failed: {exc}",
            )


class NetworkStatusCollector(BaseCollector):
    name = "network_status"
    category = EvidenceCategory.SYSTEM

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import socket

            hostname = socket.gethostname()
            try:
                ip_addr = socket.gethostbyname(hostname)
            except socket.gaierror:
                ip_addr = "unknown"

            content_parts = [f"Hostname: {hostname}", f"IP Address: {ip_addr}"]

            try:
                import psutil

                interfaces = psutil.net_if_addrs()
                for iface_name, addrs in interfaces.items():
                    for addr in addrs[:2]:
                        content_parts.append(f"  {iface_name}: {addr.address} ({addr.family})")
            except (ImportError, OSError):
                pass

            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="network_info",
                content="\n".join(content_parts),
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="network_error",
                content=f"Network status collection failed: {exc}",
            )


class RunningTasksCollector(BaseCollector):
    name = "running_tasks"
    category = EvidenceCategory.STATE

    async def collect(self, incident: Incident) -> IncidentEvidence:
        try:
            import psutil

            tasks = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    tasks.append(
                        f"  PID {proc.info['pid']}: {proc.info['name']} "
                        f"(CPU: {proc.info['cpu_percent']}%, MEM: {proc.info['memory_percent']}%)"
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            content = f"Running processes ({len(tasks)}):" + ("\n" if tasks else " none")
            if tasks:
                content += "\n" + "\n".join(tasks[:50])

            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="processes",
                content=content,
                metadata={"task_count": str(len(tasks))},
            )
        except ImportError:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="psutil_missing",
                content="psutil not installed",
            )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="tasks_error",
                content=f"Task collection failed: {exc}",
            )


class DiStateCollector(BaseCollector):
    name = "di_state"
    category = EvidenceCategory.STATE

    def __init__(self) -> None:
        self._di_state: dict | None = None

    def set_di_state(self, state: dict) -> None:
        self._di_state = state

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if self._di_state is None:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_state",
                content="No DI state available",
            )
        import json

        content = json.dumps(self._di_state, indent=2, default=str)
        return self._safe_build(
            incident,
            source=self.name,
            payload_ref="di_state",
            content=content,
        )


class GithubActionsLogCollector(BaseCollector):
    name = "github_actions_logs"
    category = EvidenceCategory.EXTERNAL

    def __init__(self, token: str | None = None, repo: str = "") -> None:
        self._token = token or __import__("os").environ.get("GITHUB_TOKEN")
        self._repo = repo

    async def collect(self, incident: Incident) -> IncidentEvidence:
        if not self._token:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="not_configured",
                content="GitHub token not configured",
            )
        if not self._repo:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="no_repo",
                content="GitHub repository not specified",
            )
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"https://api.github.com/repos/{self._repo}/actions/runs",
                    headers={"Authorization": f"token {self._token}"},
                    params={"per_page": 5},
                )
                if resp.status_code != 200:
                    return self._safe_build(
                        incident,
                        source=self.name,
                        payload_ref="api_error",
                        content=f"GitHub API returned {resp.status_code}",
                    )
                runs = resp.json().get("workflow_runs", [])
                content_parts = [f"Recent workflow runs ({len(runs)}):"]
                for run in runs:
                    content_parts.append(
                        f"  - {run.get('name', 'unknown')}: "
                        f"{run.get('conclusion', 'in_progress')} "
                        f"({run.get('created_at', 'unknown')})"
                    )
                return self._safe_build(
                    incident,
                    source=self.name,
                    payload_ref="recent_workflow_runs",
                    content="\n".join(content_parts),
                )
        except Exception as exc:
            return self._safe_build(
                incident,
                source=self.name,
                payload_ref="gh_error",
                content=f"GitHub Actions log collection failed: {exc}",
            )
