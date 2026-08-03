from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings


def test_uaes_migration_upgrade_and_downgrade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "uaes-migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    get_settings.cache_clear()

    engine = create_engine(f"sqlite:///{db_path}")
    try:
        config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        command.upgrade(config, "head")

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert {
            "uaes_health_snapshots",
            "uaes_health_components",
            "uaes_incidents",
            "uaes_incident_evidence",
            "uaes_metrics",
            "uaes_diagnostic_packs",
            "uaes_events",
        }.issubset(tables)

        command.downgrade(config, "base")
        inspector_after = inspect(engine)
        remaining = set(inspector_after.get_table_names())
        assert "uaes_health_snapshots" not in remaining
        assert "uaes_events" not in remaining
    finally:
        engine.dispose()
        get_settings.cache_clear()
