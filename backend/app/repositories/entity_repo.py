from __future__ import annotations

import json

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity, Relationship
from app.repositories.utils import escape_like
from app.schemas.entity import EntityCreate, RelationshipCreate


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, data: EntityCreate, user_id: str, embedding: str | None = None,
    ) -> Entity:
        entity = Entity(
            user_id=user_id,
            name=data.name,
            entity_type=data.entity_type,
            description=data.description,
            properties_json=json.dumps(data.properties) if data.properties else None,
            embedding_vector=embedding,
        )
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get(self, entity_id: str, user_id: str) -> Entity | None:
        result = await self.session.execute(
            select(Entity).where(Entity.id == entity_id, Entity.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, user_id: str) -> Entity | None:
        result = await self.session.execute(
            select(Entity).where(Entity.name == name, Entity.user_id == user_id),
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        user_id: str,
        entity_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Entity], int]:
        query = select(Entity).where(Entity.user_id == user_id)
        if entity_type:
            query = query.where(Entity.entity_type == entity_type)

        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery()),
        )
        total = count_result.scalar_one()

        offset = (page - 1) * page_size
        result = await self.session.execute(
            query.order_by(Entity.name).offset(offset).limit(page_size),
        )
        return list(result.scalars().all()), total

    async def search(self, query: str, user_id: str, limit: int = 20) -> list[Entity]:
        result = await self.session.execute(
            select(Entity)
            .where(
                Entity.user_id == user_id,
                Entity.name.ilike(f"%{escape_like(query)}%")
                | Entity.description.ilike(f"%{escape_like(query)}%"),
            )
            .limit(limit),
        )
        return list(result.scalars().all())

    async def update(self, entity_id: str, data: dict, user_id: str) -> Entity | None:
        entity = await self.get(entity_id, user_id)
        if not entity:
            return None
        for key, value in data.items():
            if key == "properties" and isinstance(value, dict):
                entity.properties_json = json.dumps(value)
            elif value is not None:
                setattr(entity, key, value)
        await self.session.flush()
        return entity

    async def delete(self, entity_id: str, user_id: str) -> bool:
        entity = await self.get(entity_id, user_id)
        if not entity:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def add_relationship(self, data: RelationshipCreate) -> Relationship:
        rel = Relationship(
            source_id=data.source_id,
            target_id=data.target_id,
            relation_type=data.relation_type,
            weight=data.weight,
            properties_json=json.dumps(data.properties) if data.properties else None,
        )
        self.session.add(rel)
        await self.session.flush()
        return rel

    async def get_relationships(
        self,
        entity_id: str,
        direction: str = "both",
    ) -> list[Relationship]:
        if direction == "outgoing":
            query = select(Relationship).where(Relationship.source_id == entity_id)
        elif direction == "incoming":
            query = select(Relationship).where(Relationship.target_id == entity_id)
        else:
            query = select(Relationship).where(
                (Relationship.source_id == entity_id) | (Relationship.target_id == entity_id),
            )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_neighbors(self, entity_id: str, depth: int = 1) -> list[Entity]:
        visited = set()
        current_ids = {entity_id}
        all_ids = set()

        for _ in range(depth):
            next_ids = set()
            for eid in current_ids:
                if eid in visited:
                    continue
                visited.add(eid)
                rels = await self.get_relationships(eid)
                for rel in rels:
                    neighbor_id = rel.target_id if rel.source_id == eid else rel.source_id
                    if neighbor_id not in visited:
                        next_ids.add(neighbor_id)
                        all_ids.add(neighbor_id)
            current_ids = next_ids

        if not all_ids:
            return []

        result = await self.session.execute(
            select(Entity).where(Entity.id.in_(all_ids)),
        )
        return list(result.scalars().all())
