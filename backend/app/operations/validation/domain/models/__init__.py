"""Validation Engine domain models."""

from app.operations.validation.domain.models.approval import (
    ApprovalDecision,
    ValidationExplanation,
    ValidationSignature,
)
from app.operations.validation.domain.models.assessment import (
    CompatibilityAssessment,
    CostAssessment,
    CostBreakdown,
    DependencyAssessment,
    ResourceAssessment,
    RollbackAssessment,
    SafetyAssessment,
    SafetyFactor,
    SecurityAssessment,
    SimulationAssessment,
)
from app.operations.validation.domain.models.context import (
    DependencyGraph,
    ExecutionConstraints,
    IncidentDetails,
    MonitoringSnapshot,
    RuntimeSnapshot,
    ValidationContext,
)
from app.operations.validation.domain.models.execution import (
    ExecutionBlocker,
    ExecutionPermission,
)
from app.operations.validation.domain.models.history import (
    FailingRule,
    PolicyPack,
    TrendDataPoint,
    ValidationCacheEntry,
    ValidationHistoryRecord,
    ValidationStatistics,
    ValidationTrend,
    ValidatorPlugin,
)
from app.operations.validation.domain.models.request import (
    ValidationDecision,
    ValidationEvidence,
    ValidationFailure,
    ValidationPolicy,
    ValidationRequest,
    ValidationRule,
    ValidationWarning,
)

__all__ = [
    # request.py
    "ValidationDecision",
    "ValidationEvidence",
    "ValidationFailure",
    "ValidationPolicy",
    "ValidationRequest",
    "ValidationRule",
    "ValidationWarning",
    # assessment.py
    "CompatibilityAssessment",
    "CostAssessment",
    "CostBreakdown",
    "DependencyAssessment",
    "ResourceAssessment",
    "RollbackAssessment",
    "SafetyAssessment",
    "SafetyFactor",
    "SecurityAssessment",
    "SimulationAssessment",
    # approval.py
    "ApprovalDecision",
    "ValidationExplanation",
    "ValidationSignature",
    # execution.py
    "ExecutionBlocker",
    "ExecutionPermission",
    # history.py
    "FailingRule",
    "PolicyPack",
    "TrendDataPoint",
    "ValidationCacheEntry",
    "ValidationHistoryRecord",
    "ValidationStatistics",
    "ValidationTrend",
    "ValidatorPlugin",
    # context.py
    "DependencyGraph",
    "ExecutionConstraints",
    "IncidentDetails",
    "MonitoringSnapshot",
    "RuntimeSnapshot",
    "ValidationContext",
]
