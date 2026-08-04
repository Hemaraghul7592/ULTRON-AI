from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.auth import verify_token
from app.core.database import get_session
from app.memory.knowledge_graph import KnowledgeGraphService
from app.repositories.entity_repo import EntityRepository
from app.schemas.entity import (
    EntityCreate,
    EntityResponse,
    KnowledgeGraphResponse,
    RelationshipCreate,
    RelationshipResponse,
)

router = APIRouter(prefix="/entities", tags=["entities"], dependencies=[Depends(verify_token)])


@router.get("", response_model=KnowledgeGraphResponse)
async def list_entities(
    entity_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: dict = Depends(verify_token),  # noqa: B008 FastAPI Depends() convention
) -> KnowledgeGraphResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = EntityRepository(session)
        entities, total = await repo.list_all(
            user_id=user_id, entity_type=entity_type, page=page, page_size=page_size,
        )
        return KnowledgeGraphResponse(
            entities=[EntityResponse.model_validate(e) for e in entities],
            relationships=[],
            total_entities=total,
            total_relationships=0,
        )


@router.post("", response_model=EntityResponse, status_code=201)
async def create_entity(data: EntityCreate, user: dict = Depends(verify_token)) -> EntityResponse:  # noqa: B008 FastAPI Depends() convention
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        kg = KnowledgeGraphService(session)
        entity = await kg.add_entity(
            name=data.name,
            entity_type=data.entity_type,
            description=data.description,
            properties=data.properties,
            user_id=user_id,
        )
        await session.commit()
        return EntityResponse.model_validate(entity)


@router.get("/search")
async def search_entities(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    user: dict = Depends(verify_token),  # noqa: B008 FastAPI Depends() convention
) -> list[dict]:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        kg = KnowledgeGraphService(session)
        results = await kg.search_entities(query=q, limit=limit, user_id=user_id)
        return [
            {
                "entity": EntityResponse.model_validate(r["entity"]),
                "score": r["score"],
            }
            for r in results
        ]


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(entity_id: str, user: dict = Depends(verify_token)) -> EntityResponse:  # noqa: B008 FastAPI Depends() convention
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        repo = EntityRepository(session)
        entity = await repo.get(entity_id, user_id)
        if not entity:
            from app.core.exceptions import NotFoundExceptionHTTP

            raise NotFoundExceptionHTTP("Entity", entity_id)
        return EntityResponse.model_validate(entity)


@router.post("/relationships", response_model=RelationshipResponse, status_code=201)
async def create_relationship(
    data: RelationshipCreate, user: dict = Depends(verify_token),  # noqa: B008 FastAPI Depends() convention
) -> RelationshipResponse:
    user_id = user["user_id"]
    session_factory = get_session()
    async with session_factory() as session:
        kg = KnowledgeGraphService(session)
        rel = await kg.add_relationship(
            source_name=data.source_id,
            target_name=data.target_id,
            relation_type=data.relation_type,
            weight=data.weight,
            properties=data.properties,
            user_id=user_id,
        )
        await session.commit()
        return RelationshipResponse.model_validate(rel)
