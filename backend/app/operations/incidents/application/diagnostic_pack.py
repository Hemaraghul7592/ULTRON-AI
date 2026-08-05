from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from app.operations.incidents.domain.enums import EvidenceCategory
from app.operations.incidents.domain.models import DiagnosticPack

if TYPE_CHECKING:
    from app.operations.incidents.domain.models import (
        EvidenceBundle,
        Incident,
        IncidentEvidence,
        RecoveryRecommendation,
        RootCause,
    )


class DiagnosticPackGenerator:
    def generate(
        self,
        incident: Incident,
        evidence_bundle: EvidenceBundle,
        root_cause: RootCause,
        recovery_recommendation: RecoveryRecommendation,
    ) -> DiagnosticPack:
        by_category: dict[str, list[IncidentEvidence]] = {}
        for item in evidence_bundle.evidence:
            by_category.setdefault(item.category, []).append(item)

        logs = [item.redacted_excerpt for item in by_category.get(EvidenceCategory.LOG, [])]
        stack_traces = [
            item.redacted_excerpt
            for item in by_category.get(EvidenceCategory.LOG, [])
            if item.source == "stack_traces"
        ]
        metrics = self._merge_json_payloads(by_category.get(EvidenceCategory.METRIC, []))
        configuration = self._merge_json_payloads(by_category.get(EvidenceCategory.CONFIG, []))
        health_snapshot = self._first_json_payload(
            by_category.get(EvidenceCategory.SYSTEM, []), source="health_snapshot"
        )
        git_commit = self._extract_git_commit(by_category.get(EvidenceCategory.DEPLOYMENT, []))

        timeline = self._build_timeline(incident, evidence_bundle, root_cause)
        summary = (
            f"Incident {incident.incident_id[:8]} on {incident.component_name}: "
            f"{root_cause.description}"
        )[:1000]

        return DiagnosticPack(
            incident_id=incident.incident_id,
            summary=summary,
            timeline=timeline,
            health_snapshot=health_snapshot,
            logs=logs,
            stack_traces=stack_traces,
            metrics=metrics,
            configuration=configuration,
            git_commit=git_commit,
            evidence_list=[item.evidence_id for item in evidence_bundle.evidence],
            root_cause=root_cause,
            confidence_score=root_cause.confidence,
            recovery_recommendation=recovery_recommendation,
        )

    def _merge_json_payloads(
        self, items: list[IncidentEvidence]
    ) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for item in items:
            parsed = self._parse_json(item.redacted_excerpt)
            if isinstance(parsed, dict):
                merged[item.source] = parsed
            else:
                merged[item.source] = item.redacted_excerpt
        return merged

    def _first_json_payload(
        self, items: list[IncidentEvidence], source: str
    ) -> dict[str, Any] | None:
        for item in items:
            if item.source != source:
                continue
            parsed = self._parse_json(item.redacted_excerpt)
            if isinstance(parsed, dict):
                return parsed
        return None

    def _extract_git_commit(self, items: list[IncidentEvidence]) -> str | None:
        for item in items:
            if item.source == "git_commit":
                return item.metadata.get("commit_hash")
        return None

    def _build_timeline(
        self,
        incident: Incident,
        evidence_bundle: EvidenceBundle,
        root_cause: RootCause,
    ) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        if incident.triggered_at is not None:
            timeline.append(
                {"timestamp": incident.triggered_at.isoformat(), "event": "incident_triggered"}
            )
        timeline.append(
            {
                "timestamp": evidence_bundle.collected_at.isoformat(),
                "event": "evidence_collected",
                "details": {
                    "evidence_count": len(evidence_bundle.evidence),
                    "duration_ms": evidence_bundle.collection_duration_ms,
                    "failed_collectors": evidence_bundle.failed_collectors,
                },
            }
        )
        timeline.append(
            {
                "timestamp": root_cause.determined_at.isoformat(),
                "event": "root_cause_determined",
                "details": {
                    "category": root_cause.category,
                    "rule_matched": root_cause.rule_matched,
                },
            }
        )
        return timeline

    def _parse_json(self, text: str) -> Any:
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
