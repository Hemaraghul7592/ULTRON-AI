from __future__ import annotations

import asyncio
from datetime import timedelta

from app.operations.domain.value_objects import ConfidenceScore
from app.operations.incidents.domain.enums import (
    EvidenceCategory,
    IncidentSeverity,
    IncidentStatus,
    RecommendedAction,
    RootCauseCategory,
)
from app.operations.incidents.domain.models import (
    DiagnosticPack,
    Incident,
    IncidentEvidence,
    RecoveryRecommendation,
    RootCause,
)
from app.operations.incidents.infrastructure.db.models import (
    UaesDiagnosticPackV3,
    UaesIncidentEvidenceV3,
    UaesIncidentV3,
    UaesRootCause,
)
from app.operations.incidents.infrastructure.repositories import (
    SQLAlchemyIncidentRepositoryV3,
)


def _incident(**overrides) -> Incident:
    base = {
        "severity": IncidentSeverity.HIGH,
        "component_type": "backend",
        "component_name": "api",
        "environment": "production",
        "summary": "api degraded",
        "detailed_description": "The API component is degraded",
    }
    base.update(overrides)
    return Incident(**base)


def _evidence(
    incident_id: str = "incident-1",
    category: EvidenceCategory = EvidenceCategory.LOG,
    source: str = "log",
) -> IncidentEvidence:
    return IncidentEvidence(
        incident_id=incident_id,
        category=category,
        source=source,
        payload_ref="ref",
        redacted_excerpt="test evidence content",
        checksum="c" * 32,
    )


def _root_cause(incident_id: str = "incident-1") -> RootCause:
    return RootCause(
        incident_id=incident_id,
        category=RootCauseCategory.DATABASE,
        description="database connection refused",
        confidence=ConfidenceScore(value=0.95),
        supporting_evidence=["ev-1"],
        rule_matched="database_connection_refused",
    )


def _recovery() -> RecoveryRecommendation:
    return RecoveryRecommendation(
        action=RecommendedAction.RESTART_DATABASE,
        description="restart the database",
        confidence=ConfidenceScore(value=0.85),
        estimated_impact="High",
    )


def _pack(incident_id: str = "incident-1") -> DiagnosticPack:
    return DiagnosticPack(
        incident_id=incident_id,
        summary="test diagnostic pack",
        root_cause=_root_cause(incident_id),
        confidence_score=ConfidenceScore(value=0.95),
        recovery_recommendation=_recovery(),
    )


def test_orm_incident_round_trip() -> None:
    incident = _incident(tags={"source": "test"})
    orm = UaesIncidentV3.from_domain(incident)
    restored = orm.to_domain()
    assert restored.incident_id == incident.incident_id
    assert restored.severity == incident.severity
    assert restored.component_type == incident.component_type
    assert restored.component_name == incident.component_name
    assert restored.summary == incident.summary
    assert restored.status == incident.status
    assert restored.tags == {"source": "test"}
    assert restored.confidence.value == incident.confidence.value


def test_orm_incident_duration_round_trip() -> None:
    incident = _incident()
    incident_with_duration = incident.model_copy(
        update={"duration": timedelta(seconds=120.5)}
    )
    orm = UaesIncidentV3.from_domain(incident_with_duration)
    restored = orm.to_domain()
    assert restored.duration is not None
    assert abs(restored.duration.total_seconds() - 120.5) < 0.01


def test_orm_incident_risk_score_round_trip() -> None:
    incident = _incident()
    orm = UaesIncidentV3.from_domain(incident)
    assert orm.risk_score is None


def test_orm_evidence_round_trip() -> None:
    evidence = _evidence()
    orm = UaesIncidentEvidenceV3.from_domain(evidence, incident_id="incident-1")
    restored = orm.to_domain()
    assert restored.evidence_id == evidence.evidence_id
    assert restored.category == evidence.category
    assert restored.source == evidence.source
    assert restored.redacted_excerpt == evidence.redacted_excerpt


def test_orm_root_cause_round_trip() -> None:
    root_cause = _root_cause()
    orm = UaesRootCause.from_domain(root_cause, incident_id="incident-1")
    restored = orm.to_domain()
    assert restored.root_cause_id == root_cause.root_cause_id
    assert restored.category == root_cause.category
    assert restored.description == root_cause.description
    assert restored.confidence.value == root_cause.confidence.value
    assert restored.rule_matched == root_cause.rule_matched
    assert restored.supporting_evidence == ["ev-1"]


def test_orm_diagnostic_pack_round_trip() -> None:
    pack = _pack()
    orm = UaesDiagnosticPackV3.from_domain(pack, incident_id="incident-1")
    restored = orm.to_domain()
    assert restored.pack_id == pack.pack_id
    assert restored.incident_id == pack.incident_id
    assert restored.summary == pack.summary
    assert restored.root_cause is not None
    assert restored.root_cause.category == pack.root_cause.category


def test_orm_diagnostic_pack_table_name() -> None:
    assert UaesDiagnosticPackV3.__tablename__ == "uaes_diagnostic_packs_v3"


def test_orm_incident_table_name() -> None:
    assert UaesIncidentV3.__tablename__ == "uaes_incidents_v3"


def test_repository_save_and_get() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            incident = _incident()
            await repo.save(incident)
            await session.commit()

            fetched = await repo.get(incident.incident_id)
            assert fetched is not None
            assert fetched.incident_id == incident.incident_id
            assert fetched.component_name == "api"

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_list_incidents() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc1 = _incident(component_name="svc1")
            inc2 = _incident(component_name="svc2")
            await repo.save(inc1)
            await repo.save(inc2)
            await session.commit()

            incidents = await repo.list_incidents(limit=10)
            assert len(incidents) >= 2

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_find_active() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident()
            await repo.save(inc)
            await session.commit()

            active = await repo.find_active()
            assert any(i.incident_id == inc.incident_id for i in active)

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_find_active_for_component() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident(component_type="backend", component_name="api")
            await repo.save(inc)
            await session.commit()

            found = await repo.find_active_for_component("backend", "api")
            assert any(i.incident_id == inc.incident_id for i in found)

            not_found = await repo.find_active_for_component("backend", "other")
            assert not any(i.incident_id == inc.incident_id for i in not_found)

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_add_and_get_evidence() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident()
            await repo.save(inc)
            await session.commit()

            evidence = [_evidence(incident_id=inc.incident_id)]
            await repo.add_evidence(inc.incident_id, evidence)
            await session.commit()

            fetched = await repo.get_evidence(inc.incident_id)
            assert len(fetched) == 1
            assert fetched[0].source == "log"

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_add_and_get_root_cause() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident()
            await repo.save(inc)
            await session.commit()

            rc = _root_cause(incident_id=inc.incident_id)
            await repo.add_root_cause(inc.incident_id, rc)
            await session.commit()

            fetched = await repo.get_root_cause(inc.incident_id)
            assert fetched is not None
            assert fetched.category == RootCauseCategory.DATABASE.value

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_add_and_get_diagnostic_pack() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident()
            await repo.save(inc)
            await session.commit()

            pack = _pack(incident_id=inc.incident_id)
            await repo.add_diagnostic_pack(inc.incident_id, pack)
            await session.commit()

            fetched = await repo.get_diagnostic_pack(inc.incident_id)
            assert fetched is not None
            assert fetched.incident_id == inc.incident_id

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_get_nonexistent_returns_none() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            assert await repo.get("nonexistent-id") is None
            assert await repo.get_root_cause("nonexistent-id") is None
            assert await repo.get_diagnostic_pack("nonexistent-id") is None
            assert await repo.get_evidence("nonexistent-id") == []

    asyncio.get_event_loop().run_until_complete(_run())


def test_repository_update_incident_status() -> None:
    from app.core.database import get_session

    async def _run():
        session_factory = get_session()
        async with session_factory() as session:
            repo = SQLAlchemyIncidentRepositoryV3(session)
            inc = _incident()
            await repo.save(inc)
            await session.commit()

            updated = inc.model_copy(update={"status": IncidentStatus.EVIDENCE_COLLECTED.value})
            await repo.save(updated)
            await session.commit()

            fetched = await repo.get(inc.incident_id)
            assert fetched.status == IncidentStatus.EVIDENCE_COLLECTED.value

    asyncio.get_event_loop().run_until_complete(_run())
