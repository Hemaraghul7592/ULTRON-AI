"""uaes_sprint1_foundation

Revision ID: b7c9d8e1f2a3
Revises: a1b2c3d4e5f6
Create Date: 2026-08-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c9d8e1f2a3"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uaes_health_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("overall_status", sa.String(length=20), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "uaes_health_components",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("snapshot_id", sa.String(length=36), nullable=False),
        sa.Column("component_id", sa.String(length=36), nullable=False),
        sa.Column("component_type", sa.String(length=30), nullable=False),
        sa.Column("component_name", sa.String(length=100), nullable=False),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["uaes_health_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_uaes_health_components_snapshot",
        "uaes_health_components",
        ["snapshot_id"],
        unique=False,
    )

    op.create_table(
        "uaes_incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("component", sa.String(length=30), nullable=False),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.String(length=200), nullable=False),
        sa.Column("detailed_description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("recovery_plan", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_uaes_incidents_status", "uaes_incidents", ["status", "timestamp"], unique=False
    )
    op.create_index("ix_uaes_incidents_component", "uaes_incidents", ["component"], unique=False)

    op.create_table(
        "uaes_incident_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_type", sa.String(length=40), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_ref", sa.String(length=255), nullable=False),
        sa.Column("redacted_excerpt", sa.Text(), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["uaes_incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_uaes_incident_evidence_incident",
        "uaes_incident_evidence",
        ["incident_id"],
        unique=False,
    )

    op.create_table(
        "uaes_metrics",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("metric_type", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("component", sa.String(length=30), nullable=True),
        sa.Column("environment", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["uaes_incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_uaes_metrics_name", "uaes_metrics", ["name", "observed_at"], unique=False)
    op.create_index(
        "ix_uaes_metrics_type", "uaes_metrics", ["metric_type", "observed_at"], unique=False
    )

    op.create_table(
        "uaes_diagnostic_packs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("incident_id", sa.String(length=36), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.String(length=1000), nullable=False),
        sa.Column("log_ref", sa.String(length=255), nullable=True),
        sa.Column("metric_ref", sa.String(length=255), nullable=True),
        sa.Column("config_ref", sa.String(length=255), nullable=True),
        sa.Column("environment_ref", sa.String(length=255), nullable=True),
        sa.Column("commit_ref", sa.String(length=255), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["incident_id"], ["uaes_incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_uaes_diagnostic_packs_incident", "uaes_diagnostic_packs", ["incident_id"], unique=False
    )

    op.create_table(
        "uaes_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=36), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("correlation_id", sa.String(length=36), nullable=True),
        sa.Column("causation_id", sa.String(length=36), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_uaes_events_aggregate",
        "uaes_events",
        ["aggregate_type", "aggregate_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_uaes_events_type", "uaes_events", ["event_type", "occurred_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_uaes_events_type", table_name="uaes_events")
    op.drop_index("ix_uaes_events_aggregate", table_name="uaes_events")
    op.drop_table("uaes_events")

    op.drop_index("ix_uaes_diagnostic_packs_incident", table_name="uaes_diagnostic_packs")
    op.drop_table("uaes_diagnostic_packs")

    op.drop_index("ix_uaes_metrics_type", table_name="uaes_metrics")
    op.drop_index("ix_uaes_metrics_name", table_name="uaes_metrics")
    op.drop_table("uaes_metrics")

    op.drop_index("ix_uaes_incident_evidence_incident", table_name="uaes_incident_evidence")
    op.drop_table("uaes_incident_evidence")

    op.drop_index("ix_uaes_incidents_component", table_name="uaes_incidents")
    op.drop_index("ix_uaes_incidents_status", table_name="uaes_incidents")
    op.drop_table("uaes_incidents")

    op.drop_index("ix_uaes_health_components_snapshot", table_name="uaes_health_components")
    op.drop_table("uaes_health_components")

    op.drop_table("uaes_health_snapshots")
