from __future__ import annotations

from app.core.database import Base


def test_uaes_tables_present_in_metadata() -> None:
    tables = set(Base.metadata.tables)
    assert {
        "uaes_health_snapshots",
        "uaes_health_components",
        "uaes_incidents",
        "uaes_incident_evidence",
        "uaes_metrics",
        "uaes_diagnostic_packs",
        "uaes_events",
    }.issubset(tables)
