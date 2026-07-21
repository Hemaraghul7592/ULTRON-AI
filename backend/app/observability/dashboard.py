from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.observability.metrics import MetricsService
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.memory_repo import MemoryRepository
from app.repositories.task_repo import JobRepository, TaskRepository
from app.repositories.token_repo import TokenRepository


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.metrics = MetricsService(session)
        self.conversation_repo = ConversationRepository(session)
        self.memory_repo = MemoryRepository(session)
        self.task_repo = TaskRepository(session)
        self.job_repo = JobRepository(session)
        self.token_repo = TokenRepository(session)

    async def get_dashboard(self, user_id: str) -> dict[str, Any]:
        _, total_conversations = await self.conversation_repo.list_all(user_id=user_id, page=1, page_size=1)
        _, total_memories = await self.memory_repo.list_all(user_id=user_id, page=1, page_size=1)
        _, total_tasks = await self.task_repo.list_all(user_id=user_id, page=1, page_size=1)
        active_tasks_data, _ = await self.task_repo.list_all(user_id=user_id, page=1, page_size=1, status="pending")
        active_tasks = len(active_tasks_data)

        _, total_jobs = await self.job_repo.list_all(page=1, page_size=1)
        failed_jobs_data, _ = await self.job_repo.list_all(page=1, page_size=1)

        token_totals = await self.token_repo.get_totals(hours=24)
        provider_usage = await self.token_repo.get_by_provider(hours=24)

        latency = await self.metrics.get_latency_percentiles(hours=24)
        recent_metrics = await self.metrics.get_recent_metrics(limit=20)
        uptime = self.metrics.get_uptime()

        return {
            "total_conversations": total_conversations,
            "total_messages": 0,
            "total_memories": total_memories,
            "total_tasks": total_tasks,
            "total_tokens_used": token_totals["total_tokens"],
            "total_cost_usd": token_totals["total_cost_usd"],
            "active_tasks": active_tasks,
            "failed_jobs": len(failed_jobs_data),
            "provider_usage": provider_usage,
            "recent_metrics": recent_metrics,
            "latency_p50": latency["p50"],
            "latency_p95": latency["p95"],
            "latency_p99": latency["p99"],
            "uptime_seconds": uptime,
        }
