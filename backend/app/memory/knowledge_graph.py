from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.memory.embeddings import EmbeddingService
from app.repositories.entity_repo import EntityRepository
from app.schemas.entity import EntityCreate, RelationshipCreate

logger = get_logger(__name__)


class KnowledgeGraphService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = EntityRepository(session)
        self.embedding_service = EmbeddingService()

    async def add_entity(
        self,
        name: str,
        entity_type: str,
        description: str | None = None,
        properties: dict | None = None,
        user_id: str = "",
    ) -> Any:
        existing = await self.repo.get_by_name(name, user_id=user_id)
        if existing:
            return existing

        embedding = await self.embedding_service.embed(f"{name} {description or ''}")
        embedding_str = self.embedding_service.serialize_vector(embedding)
        data = EntityCreate(
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties,
        )
        entity = await self.repo.create(data, user_id=user_id, embedding=embedding_str)
        logger.info("entity_created", entity_id=entity.id, name=name, type=entity_type)
        return entity

    async def add_relationship(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        weight: float = 1.0,
        properties: dict | None = None,
        user_id: str = "",
    ) -> Any:
        source = await self.repo.get_by_name(source_name, user_id=user_id)
        if not source:
            source = await self.add_entity(source_name, "concept", user_id=user_id)

        target = await self.repo.get_by_name(target_name, user_id=user_id)
        if not target:
            target = await self.add_entity(target_name, "concept", user_id=user_id)

        data = RelationshipCreate(
            source_id=source.id,
            target_id=target.id,
            relation_type=relation_type,
            weight=weight,
            properties=properties,
        )
        rel = await self.repo.add_relationship(data)
        logger.info(
            "relationship_created",
            source=source_name,
            target=target_name,
            type=relation_type,
        )
        return rel

    async def search_entities(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        text_results = await self.repo.search(query, user_id=user_id, limit=limit * 2)

        query_embedding = await self.embedding_service.embed(query)
        scored: list[dict[str, Any]] = []

        for entity in text_results:
            score = 0.0
            if entity.name.lower() in query.lower():
                score += 0.5
            if entity.embedding_vector:
                ent_embedding = self.embedding_service.deserialize_vector(entity.embedding_vector)
                sim = self.embedding_service.cosine_similarity(query_embedding, ent_embedding)
                score += sim * 0.5

            if score > 0:
                scored.append({"entity": entity, "score": score})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    async def get_entity_context(
        self, entity_name: str, user_id: str, depth: int = 2
    ) -> dict[str, Any]:
        entity = await self.repo.get_by_name(entity_name, user_id=user_id)
        if not entity:
            return {"entity": None, "neighbors": [], "relationships": []}

        neighbors = await self.repo.get_neighbors(entity.id, depth=depth)
        relationships = await self.repo.get_relationships(entity.id)

        return {
            "entity": entity,
            "neighbors": neighbors,
            "relationships": relationships,
        }

    async def get_stats(self, user_id: str) -> dict[str, Any]:
        entities, total = await self.repo.list_all(user_id=user_id, page=1, page_size=1)
        return {
            "total_entities": total,
        }
