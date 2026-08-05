from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.operations.validation.application.dto import (
        HistoricalPredictionDTO,
        RecurringFailureSummaryDTO,
    )
    from app.operations.validation.domain.models import (
        ValidationHistoryRecord,
        ValidationStatistics,
    )


class ValidationHistoryRepository(Protocol):
    """Abstract repository for validation history persistence and queries."""

    async def save_history(self, record: ValidationHistoryRecord) -> None:
        """Persist a validation history record."""
        ...

    async def get_history_by_plan(self, plan_id: str) -> list[ValidationHistoryRecord]:
        """Retrieve all history records for a given plan."""
        ...

    async def get_history_by_incident(self, incident_id: str) -> list[ValidationHistoryRecord]:
        """Retrieve all history records for a given incident."""
        ...

    async def get_statistics(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        environment: str | None = None,
    ) -> ValidationStatistics:
        """Retrieve aggregated validation statistics for a period."""
        ...

    async def get_false_positives(self, limit: int = 100) -> list[ValidationHistoryRecord]:
        """Retrieve approved plans that failed during execution."""
        ...

    async def get_false_negatives(self, limit: int = 100) -> list[ValidationHistoryRecord]:
        """Retrieve rejected plans that would have succeeded."""
        ...

    async def get_recurring_failures(
        self,
        *,
        rule_code: str | None = None,
        limit: int = 100,
    ) -> list[RecurringFailureSummaryDTO]:
        """Retrieve rules that fail repeatedly."""
        ...

    async def predict_outcome(
        self,
        request_id: str,
    ) -> HistoricalPredictionDTO:
        """Predict validation outcome based on historical patterns."""
        ...
