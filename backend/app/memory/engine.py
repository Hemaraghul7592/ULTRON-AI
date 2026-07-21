from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.memory.embeddings import EmbeddingService
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import MemoryCreate

logger = get_logger(__name__)


class MemoryEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = MemoryRepository(session)
        self.embedding_service = EmbeddingService()
        self._initialized = False

    async def initialize(self) -> None:
        if not self._initialized:
            await self.embedding_service.initialize()
            self._initialized = True

    async def store(self, data: MemoryCreate, user_id: str) -> Any:
        embedding = await self.embedding_service.embed(data.content)
        embedding_str = self.embedding_service.serialize_vector(embedding)
        memory = await self.repo.create(data, user_id=user_id, embedding=embedding_str)
        logger.info(
            "memory_stored",
            memory_id=memory.id,
            memory_type=memory.memory_type,
            importance=memory.importance,
        )
        return memory

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        memory_type: str | None = None,
        min_importance: float = 0.0,
    ) -> list[dict[str, Any]]:
        text_results = await self.repo.search_by_content(query, user_id=user_id, limit=limit * 2, memory_type=memory_type)

        query_embedding = await self.embedding_service.embed(query)
        scored_results: list[dict[str, Any]] = []

        for memory in text_results:
            text_score = 0.0
            if memory.content:
                query_words = set(query.lower().split())
                content_words = set(memory.content.lower().split())
                overlap = query_words & content_words
                text_score = len(overlap) / max(len(query_words), 1) * 0.5

            embedding_score = 0.0
            if memory.embedding_vector:
                mem_embedding = self.embedding_service.deserialize_vector(memory.embedding_vector)
                embedding_score = self.embedding_service.cosine_similarity(query_embedding, mem_embedding) * 0.5

            combined_score = text_score + embedding_score
            if combined_score > 0 and memory.importance >= min_importance:
                scored_results.append({
                    "memory": memory,
                    "score": combined_score,
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:limit]

    async def get_context_for_query(self, query: str, user_id: str, limit: int = 5) -> str:
        results = await self.search(query, user_id=user_id, limit=limit)
        if not results:
            return ""
        lines = []
        for r in results:
            mem = r["memory"]
            lines.append(f"- {mem.content}")
        return "\n".join(lines)

    async def promote_important_memories(self, user_id: str) -> int:
        settings = get_settings()
        promoted = await self.repo.promote_to_long_term(
            user_id=user_id, threshold=settings.MEMORY_LONG_TERM_THRESHOLD
        )
        if promoted > 0:
            logger.info("memories_promoted", count=promoted)
        return promoted

    async def summarize_and_compress(self, user_id: str) -> int:
        settings = get_settings()
        short_term = await self.repo.get_by_type("short_term", user_id=user_id, limit=100)
        if len(short_term) < settings.MEMORY_SUMMARIZATION_THRESHOLD:
            return 0

        summaries = []
        for mem in short_term:
            summaries.append(mem.content)

        summary_text = " | ".join(summaries[:20])
        from app.schemas.memory import MemoryCreate

        summary_data = MemoryCreate(
            content=f"Summary of {len(short_term)} short-term memories: {summary_text[:2000]}",
            memory_type="long_term",
            importance=0.8,
            source="memory_engine",
            tags=["summary", "auto-generated"],
        )
        await self.store(summary_data, user_id=user_id)

        for mem in short_term[:10]:
            await self.repo.delete(mem.id, user_id=user_id)

        logger.info("memories_summarized", compressed=len(short_term[:10]))
        return len(short_term[:10])

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        short_term, st_total = await self.repo.list_all(user_id=user_id, page=1, page_size=1, memory_type="short_term")
        long_term, lt_total = await self.repo.list_all(user_id=user_id, page=1, page_size=1, memory_type="long_term")
        return {
            "short_term_count": st_total,
            "long_term_count": lt_total,
            "total_memories": st_total + lt_total,
        }