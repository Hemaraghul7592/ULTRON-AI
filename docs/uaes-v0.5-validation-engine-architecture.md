# UAES v0.5 — Validation Engine Architecture Specification

> **Status**: ARCHITECTURE REVIEW — Revised draft with improvements
> **Version**: 0.5.0
> **Date**: 2026-08-05
> **Owner**: ULTRON Core Team
> **Classification**: Internal Engineering Reference

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Responsibilities](#2-responsibilities)
3. [Architecture](#3-architecture)
4. [Validation Context](#4-validation-context)
5. [Domain Models](#5-domain-models)
6. [Value Objects](#6-value-objects)
7. [Enums](#7-enums)
8. [Repositories](#8-repositories)
9. [Services](#9-services)
10. [Validation Rules](#10-validation-rules)
11. [Approval Policy](#11-approval-policy)
12. [Validation Pipeline](#12-validation-pipeline)
13. [Database](#13-database)
14. [REST API](#14-rest-api)
15. [Events](#15-events)
16. [Integration](#16-integration)
17. [Learning Integration](#17-learning-integration)
18. [Architecture Constraints](#18-architecture-constraints)
19. [Failure Modes](#19-failure-modes)
20. [Security](#20-security)
21. [Performance](#21-performance)
22. [Testing Strategy](#22-testing-strategy)
23. [Definition of Done](#23-definition-of-done)
24. [Validation History Intelligence](#24-validation-history-intelligence)
25. [Explainable Validation](#25-explainable-validation)
26. [AI Validator Extension Point](#26-ai-validator-extension-point)
27. [Validation Cache](#27-validation-cache)
28. [Digital Signature](#28-digital-signature)
29. [Validation Trend Analysis](#29-validation-trend-analysis)
30. [Generic Validation Framework](#30-generic-validation-framework)
31. [Policy Packs](#31-policy-packs)
32. [Validator Plugin System](#32-validator-plugin-system)
33. [Future Integration](#33-future-integration)

**Appendices**:
- [Appendix A: UAES System Architecture](#appendix-a-uaes-system-architecture)
- [Appendix B: Dependency Graph](#appendix-b-dependency-graph)
- [Appendix C: Data Flow](#appendix-c-data-flow)
- [Appendix D: Enum Reference](#appendix-d-enum-reference)
- [Appendix E: Checklist Summary](#appendix-e-checklist-summary)

---

## 1. Purpose

### 1.1 Why It Exists

The ULTRON Autonomous Execution System (UAES) enables autonomous repair and remediation of infrastructure incidents. The Validation Engine is the **final safety gate** between the Planner (which generates repair plans) and the Execution Engine (which carries out those plans). Without the Validation Engine, the system would execute arbitrary repairs with no safety guarantee.

The Validation Engine is a **generic validation framework** that supports validating:
- Infrastructure repair plans
- Deployment plans
- Automation plans
- Financial strategies
- Stock trading strategies
- AI workflows
- Future autonomous tasks

The Validation Engine answers a single question: **"Should this plan be allowed to execute?"**

### 1.2 Problems It Solves

| Problem | Solution |
|---------|----------|
| Blind autonomous execution | Every plan passes through 20+ validation dimensions |
| No rollback safety net | Rollback feasibility assessment before execution |
| Insufficient human oversight | 6-level approval hierarchy with escalation |
| Unbounded blast radius | Dependency graph analysis with cascade risk scoring |
| Configuration drift | Compatibility checks across config, environment, and version |
| Resource exhaustion | Resource availability verification before execution |
| Compliance violations | Policy pack enforcement with hard/soft modes |
| No audit trail | Immutable audit log with hash-chain integrity |
| Catastrophic actions | Hard blocks on destructive operations |
| Cost overruns | Budget compliance checks with threshold enforcement |
| No explainability | Every decision includes detailed reasoning |
| Untraceable decisions | Digital signatures on approved plans |
| No historical intelligence | Validation history with trend analysis |
| No extensibility | Plugin system for custom validators |

### 1.3 Defense-in-Depth Layers

The Validation Engine implements six nested defense layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT LAYER                              │
│  Immutable log of every validation, decision, and action    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 SIGNATURE LAYER                      │   │
│  │  Digital signatures on approved plans                │   │
│  │  ┌───────────────────────────────────────────────┐   │   │
│  │  │              APPROVAL LAYER                   │   │   │
│  │  │  Human approval with 6-level hierarchy        │   │   │
│  │  │  ┌────────────────────────────────────────┐   │   │   │
│  │  │  │           POLICY LAYER                 │   │   │   │
│  │  │  │  Policy packs with hard/soft enforce   │   │   │   │
│  │  │  │  ┌─────────────────────────────────┐   │   │   │   │
│  │  │  │  │         RULE LAYER              │   │   │   │   │
│  │  │  │  │  40+ configurable validation    │   │   │   │   │
│  │  │  │  │  rules across 8 categories     │   │   │   │   │
│  │  │  │  └─────────────────────────────────┘   │   │   │   │
│  │  │  └────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Rule Layer**: Evaluates 40+ configurable rules across 8 categories. Rules produce blockers (hard stops) and warnings (advisory).

**Policy Layer**: Enforces policy packs. Policies are typed with hard enforcement (blocks) or soft enforcement (warns).

**Approval Layer**: 6-level human approval hierarchy (AUTO → DEVELOPER → MAINTAINER → OPERATIONS → ADMINISTRATOR → EMERGENCY). Emergency override with audit. Timeout-based escalation.

**Signature Layer**: Digital signatures on approved plans. Execution Engine verifies signatures before execution.

**Audit Layer**: Immutable audit log with hash-chain integrity. Every validation, decision, approval, and permission change is recorded.

### 1.4 Position in UAES

The Validation Engine is stage 5 of the 7-stage ULTRON Autonomous Execution System:

```
┌──────────────────┐
│    MONITORING    │ ◄──── Stage 1: Detect health changes
│                  │
└────────┬─────────┘
         │ HealthChanged
         ▼
┌──────────────────┐
│   INCIDENT       │ ◄──── Stage 2: Create incidents
│   DETECTION      │
└────────┬─────────┘
         │ IncidentCreated
         ▼
┌──────────────────┐
│   ROOT CAUSE     │ ◄──── Stage 3: Determine probable cause
│   ANALYSIS       │
└────────┬─────────┘
         │ RootCauseDetermined
         ▼
┌──────────────────┐
│    PLANNER       │ ◄──── Stage 4: Produce repair plans
│                  │
└────────┬─────────┘
         │ PlanGenerated
         ▼
┌──────────────────┐
│   VALIDATION     │ ◄──── Stage 5: Verify every repair
│   ENGINE         │
└────────┬─────────┘
         │ ValidationCompleted
         ▼
┌──────────────────┐
│   EXECUTION      │ ◄──── Stage 6: Execute approved repairs
│   ENGINE         │
└────────┬─────────┘
         │ ExecutionCompleted
         ▼
┌──────────────────┐
│    LEARNING      │ ◄──── Stage 7: Learn from outcomes
│    ENGINE        │
└──────────────────┘

Feedback Loops:
- Learning → Monitoring: Updated health thresholds
- Learning → Planner: Improved strategy selection
- Learning → Validation: Improved rule accuracy
- Learning → Execution: Improved rollback strategies
```

---

## 2. Responsibilities

### 2.1 Validation Dimensions

The Validation Engine evaluates every plan against 20+ dimensions:

| # | Dimension | Description | Severity if Failed |
|---|-----------|-------------|-------------------|
| 1 | **Repair Safety** | Is the repair inherently safe to execute? | BLOCKER |
| 2 | **Dependency Impact** | What services/components are affected? | BLOCKER or WARNING |
| 3 | **Configuration Compatibility** | Are configurations compatible? | BLOCKER |
| 4 | **Environment Compatibility** | Is the environment suitable? | BLOCKER |
| 5 | **Version Compatibility** | Are versions compatible? | BLOCKER |
| 6 | **Risk Score** | What is the aggregate risk (0-100)? | BLOCKER if >95 |
| 7 | **Confidence Score** | How confident are we in the repair (0.0-1.0)? | WARNING if <0.5 |
| 8 | **Execution Constraints** | Time, duration, ordering constraints met? | BLOCKER |
| 9 | **Security Constraints** | Auth, permissions, audit requirements met? | BLOCKER |
| 10 | **Permission Requirements** | Does the actor have required permissions? | BLOCKER |
| 11 | **Rollback Feasibility** | Can we roll back if the repair fails? | BLOCKER or WARNING |
| 12 | **Simulation Success** | Did the simulation pass? | WARNING |
| 13 | **Resource Availability** | CPU, memory, disk, network available? | BLOCKER |
| 14 | **Human Approval Policy** | Does this require human approval? | BLOCKER |
| 15 | **Maintenance Window** | Is this within the maintenance window? | BLOCKER |
| 16 | **Production Policy** | Does this comply with production policies? | BLOCKER |
| 17 | **Business Policy** | Does this comply with business policies? | BLOCKER or WARNING |
| 18 | **Cost Impact** | What is the operational and human cost? | WARNING or BLOCKER |
| 19 | **Historical Patterns** | Does this match known failure patterns? | WARNING |
| 20 | **AI Assessment** | What does the AI validator recommend? | INFO or WARNING |

### 2.2 Non-Responsibilities

- **Plan Generation**: The Planner generates repair plans. The Validation Engine only validates them.
- **Plan Execution**: The Execution Engine carries out approved plans. The Validation Engine only grants/denies permission.
- **Monitoring**: The Monitoring Engine observes system health. The Validation Engine reads health data but does not emit metrics.
- **Incident Detection**: The Incident system detects problems. The Validation Engine reads incident metadata.

---

## 3. Architecture

### 3.1 Bounded Context

The Validation Engine is a standalone bounded context within the ULTRON backend. It has its own domain, application, infrastructure, and API layers. It depends on nothing outside its context boundary except shared kernel types (UUID, datetime, enums).

### 3.2 Folder Structure

```
backend/app/operations/validation/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── models.py                    # All domain models
│   ├── value_objects.py             # All value objects
│   ├── enums.py                     # All enums
│   ├── events.py                    # All domain events
│   └── rules.py                     # Validation rule definitions
├── application/
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── repositories.py          # Repository protocols
│   │   └── event_publisher.py       # Event publisher protocol
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validation_service.py    # Orchestrator
│   │   ├── rule_engine.py           # Rule evaluation
│   │   ├── policy_engine.py         # Policy evaluation
│   │   ├── approval_engine.py       # Approval workflow
│   │   ├── dependency_analyzer.py   # Dependency analysis
│   │   ├── compatibility_analyzer.py
│   │   ├── rollback_analyzer.py
│   │   ├── security_analyzer.py
│   │   ├── simulation_verifier.py
│   │   ├── environment_analyzer.py
│   │   ├── resource_analyzer.py
│   │   ├── decision_engine.py       # Final decision
│   │   ├── summary_generator.py     # Human-readable summary
│   │   ├── explainability_service.py # Explainability
│   │   ├── history_service.py       # Validation history
│   │   ├── trend_service.py         # Trend analysis
│   │   └── cache_service.py         # Validation cache
│   └── pipeline/
│       ├── __init__.py
│       └── stages.py                # Pipeline stage definitions
├── infrastructure/
│   ├── __init__.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── repositories/            # Repository implementations
│   │   └── migrations/              # Alembic migrations
│   ├── event_bus/
│   │   └── in_process_event_publisher.py
│   ├── cache/
│   │   └── validation_cache.py
│   └── plugins/
│       ├── __init__.py
│       └── plugin_manager.py        # Plugin discovery and loading
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py
│       ├── router.py
│       └── schemas.py
└── tests/
    ├── unit/
    ├── integration/
    ├── stress/
    └── chaos/
```

### 3.3 Clean Architecture / DDD Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  Routes, Request/Response schemas, Dependencies             │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                          │
│  Services, Pipeline, Ports (interfaces)                     │
│  Imports: domain (models, value_objects, enums, events)     │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│  Models, Value Objects, Enums, Events                       │
│  Imports: NOTHING (pure domain)                             │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                        │
│  SQLAlchemy models, Repository implementations              │
│  Event bus, Cache, Plugins, External adapters               │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Validation Context

### 4.1 Purpose

The Validation Context is the **single source of truth** for the entire validation pipeline. It replaces the previous architecture where analyzers received many independent parameters. Instead, every analyzer receives only the context:

```python
# OLD ARCHITECTURE (rejected)
result = await analyzer.analyze(
    request,
    incident,
    planner,
    monitoring,
    resources,
    dependency_graph,
    policies,
    runtime,
    evidence,
)

# NEW ARCHITECTURE (adopted)
result = await analyzer.analyze(context)
```

### 4.2 Why It Exists

| Problem | Solution |
|---------|----------|
| Analyzer signature explosion | Single `context` parameter |
| Inconsistent data access | Centralized, immutable context |
| Difficult to test | Mock one context object |
| Race conditions | Immutable during validation |
| Hidden dependencies | Explicit context fields |
| Difficult to audit | Complete validation state in one object |

### 4.3 Why Every Analyzer Depends on It

Every analyzer needs access to the same validation state. Without a shared context:
- Analyzers receive different subsets of data
- Data inconsistency between analyzers
- Testing requires mocking many objects
- Auditing requires reconstructing state from scattered sources

With a shared context:
- All analyzers see the same data
- Data is consistent across the pipeline
- Testing requires mocking one object
- Auditing has complete state in one place

### 4.4 ValidationContext Model

```python
class ValidationContext(BaseModel):
    """
    Immutable validation context. Single source of truth for the pipeline.
    Built by ValidationService. Read-only for all analyzers.
    """
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    # ── Request ──────────────────────────────────────────────
    request: ValidationRequest                    # The original validation request

    # ── Planner Result ───────────────────────────────────────
    planner_result: dict[str, Any]                # Serialized planner output
    planner_strategy: str | None = None           # Strategy used by planner
    planner_confidence: float | None = None       # Planner's confidence score

    # ── Monitoring Snapshot ──────────────────────────────────
    monitoring_snapshot: MonitoringSnapshot        # Current system health
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_usage_gb: float = 0.0
    network_latency_ms: float = 0.0
    active_incidents: list[str] = []              # Currently active incidents

    # ── Incident ─────────────────────────────────────────────
    incident: IncidentDetails | None = None       # Associated incident details
    incident_severity: str | None = None          # "low", "medium", "high", "critical"
    incident_category: str | None = None          # Root cause category
    incident_age_hours: float | None = None       # How long incident has been active

    # ── Dependency Graph ─────────────────────────────────────
    dependency_graph: DependencyGraph             # Service dependency graph
    affected_components: list[str] = []           # Components affected by plan
    reverse_dependencies: list[str] = []          # Services that depend on affected
    critical_path: list[str] = []                 # Critical path services

    # ── Policy Pack ──────────────────────────────────────────
    policy_pack: PolicyPack                       # Selected policy pack
    active_policies: list[ValidationPolicy] = []  # Policies to evaluate
    enforcement_mode: str = "hard"                # "hard" or "soft"

    # ── Runtime Snapshot ─────────────────────────────────────
    runtime_snapshot: RuntimeSnapshot             # Current runtime state
    active_deployments: list[str] = []            # Currently deploying services
    maintenance_window_active: bool = False       # Is maintenance window active?
    deployment_in_progress: bool = False          # Is a deployment happening?

    # ── Collected Evidence ───────────────────────────────────
    collected_evidence: list[ValidationEvidence] = []  # Evidence collected so far

    # ── Execution Constraints ────────────────────────────────
    execution_constraints: ExecutionConstraints   # Time, resource, ordering constraints
    max_execution_time_seconds: int = 3600        # Maximum allowed execution time
    required_approvals: list[str] = []            # Required approval roles
    blocked_time_ranges: list[TimeRange] = []     # Times when execution is blocked

    # ── Historical Context ───────────────────────────────────
    historical_failures: int = 0                  # Past failures for this pattern
    false_positive_rate: float = 0.0              # Historical false positive rate
    similar_plan_outcomes: list[str] = []         # Outcomes of similar past plans

    # ── Metadata ─────────────────────────────────────────────
    metadata: dict[str, Any] = {}                 # Arbitrary metadata
    built_at: datetime                            # When context was built
    built_by: str = "system"                      # Who built the context
```

### 4.5 Context Construction

Only `ValidationService` may build the `ValidationContext`:

```python
class ValidationService:
    async def _build_context(
        self,
        request: ValidationRequest,
    ) -> ValidationContext:
        """Build the immutable validation context."""
        # 1. Fetch planner result
        planner_result = await self._planner_repository.get_result(request.plan_id)

        # 2. Fetch monitoring snapshot
        monitoring_snapshot = await self._monitoring_service.get_snapshot()

        # 3. Fetch incident details (if any)
        incident = None
        if request.incident_id:
            incident = await self._incident_service.get_details(request.incident_id)

        # 4. Fetch dependency graph
        dependency_graph = await self._dependency_service.get_graph()

        # 5. Select policy pack
        policy_pack = await self._policy_pack_loader.select_pack(request)
        active_policies = await self._policy_pack_loader.load_policies(policy_pack)

        # 6. Fetch runtime snapshot
        runtime_snapshot = await self._runtime_service.get_snapshot()

        # 7. Fetch historical context
        historical = await self._history_service.get_context(request.plan_id)

        return ValidationContext(
            request=request,
            planner_result=planner_result,
            planner_strategy=planner_result.get("strategy"),
            planner_confidence=planner_result.get("confidence"),
            monitoring_snapshot=monitoring_snapshot,
            cpu_usage_percent=monitoring_snapshot.cpu_usage,
            memory_usage_mb=monitoring_snapshot.memory_usage,
            disk_usage_gb=monitoring_snapshot.disk_usage,
            network_latency_ms=monitoring_snapshot.network_latency,
            active_incidents=monitoring_snapshot.active_incidents,
            incident=incident,
            incident_severity=incident.severity if incident else None,
            incident_category=incident.category if incident else None,
            incident_age_hours=incident.age_hours if incident else None,
            dependency_graph=dependency_graph,
            affected_components=self._extract_affected_components(request, dependency_graph),
            reverse_dependencies=self._extract_reverse_dependencies(request, dependency_graph),
            critical_path=self._extract_critical_path(request, dependency_graph),
            policy_pack=policy_pack,
            active_policies=active_policies,
            enforcement_mode=policy_pack.enforcement_mode,
            runtime_snapshot=runtime_snapshot,
            active_deployments=runtime_snapshot.active_deployments,
            maintenance_window_active=runtime_snapshot.maintenance_window_active,
            deployment_in_progress=runtime_snapshot.deployment_in_progress,
            collected_evidence=[],
            execution_constraints=self._extract_constraints(request, policy_pack),
            max_execution_time_seconds=self._compute_max_execution_time(request),
            required_approvals=self._compute_required_approvals(request, policy_pack),
            blocked_time_ranges=self._compute_blocked_times(request, policy_pack),
            historical_failures=historical.failures,
            false_positive_rate=historical.false_positive_rate,
            similar_plan_outcomes=historical.similar_outcomes,
            metadata={},
            built_at=datetime.utcnow(),
            built_by="system",
        )
```

### 4.6 Immutability Rules

| Rule | Description |
|------|-------------|
| **Immutable during run** | Once built, the context cannot be modified |
| **Read-only for analyzers** | Analyzers may only read from the context |
| **No mutation** | No analyzer may call `model_copy()` on the context |
| **Evidence accumulation** | New evidence is added by returning it, not mutating context |
| **Only ValidationService builds** | No other service may construct a context |

### 4.7 Analyzer Contract

Every analyzer must follow this contract:

```python
class AnalyzerProtocol(Protocol):
    """Protocol for all analyzers."""

    async def analyze(
        self,
        context: ValidationContext,
    ) -> Assessment:
        """
        Analyze the plan using the provided context.

        Rules:
        1. READ from context only
        2. DO NOT mutate context
        3. RETURN assessment with evidence
        4. Evidence is accumulated by ValidationService
        """
        ...
```

### 4.8 Evidence Accumulation

Analyzers return evidence, which ValidationService accumulates:

```python
class ValidationService:
    async def _run_pipeline(
        self,
        context: ValidationContext,
    ) -> ValidationDecision:
        """Run the validation pipeline."""
        all_evidence = []
        all_failures = []
        all_warnings = []

        # Run analyzers (each returns evidence, no mutation)
        safety_evidence = await self._safety_analyzer.analyze(context)
        all_evidence.extend(safety_evidence.evidence)

        dependency_evidence = await self._dependency_analyzer.analyze(context)
        all_evidence.extend(dependency_evidence.evidence)

        # ... more analyzers ...

        # Build new context with accumulated evidence (immutably)
        context_with_evidence = context.model_copy(update={
            "collected_evidence": all_evidence,
        })

        # Continue pipeline with enriched context
        return await self._run_rules_and_decide(context_with_evidence)
```

### 4.9 Testing Benefits

With a single context object, testing becomes straightforward:

```python
async def test_safety_analyzer_blocks_catastrophic_risk():
    # Arrange: Build a test context
    context = ValidationContext(
        request=ValidationRequest(...),
        planner_result={"risk_score": 95},
        monitoring_snapshot=MonitoringSnapshot(...),
        incident=IncidentDetails(severity="critical"),
        dependency_graph=DependencyGraph(...),
        policy_pack=PolicyPack(...),
        runtime_snapshot=RuntimeSnapshot(...),
        execution_constraints=ExecutionConstraints(...),
        built_at=datetime.utcnow(),
    )

    # Act: Run the analyzer
    analyzer = SafetyAnalyzer()
    result = await analyzer.analyze(context)

    # Assert: Check the result
    assert result.risk_score.value >= 90
    assert result.requires_human_approval is True
```

### 4.10 Audit Benefits

The context provides complete audit trail:

```python
# Every validation run has a complete, immutable context
context = await validation_service._build_context(request)

# The context can be stored for audit
await audit_repository.save_context(context)

# Later, auditors can inspect exactly what data was used
stored_context = await audit_repository.get_context(request_id)
```

---

## 5. Domain Models

All domain models are Pydantic `BaseModel` with `frozen=True` and `model_config = ConfigDict(use_enum_values=True)`. Mutations use `model_copy(update={...})`.

### 5.1 ValidationRequest

Entry point from the Planner. Immutable request to validate a plan.

```python
class ValidationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    request_id: str                              # UUID, auto-generated
    plan_id: str                                 # Reference to the plan being validated
    incident_id: str | None                      # Associated incident (if any)
    plan_json: dict[str, Any]                    # Serialized plan for validation
    plan_type: str = "infrastructure_repair"     # Plan type for generic validation
    environment: str                             # "development" | "staging" | "production"
    requested_by: str                            # Actor who requested validation
    requested_at: datetime                       # When the request was made
    priority: int = 0                            # Higher = validate first
    timeout_seconds: int = 300                   # Validation timeout (default 5min)
    metadata: dict[str, Any] = {}                # Arbitrary metadata
```

### 5.2 ValidationDecision

Enum-based decision outcome with full explainability.

```python
class ValidationDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision: ValidationDecisionEnum              # Final decision
    decision_reason: str                          # Human-readable reason
    decided_at: datetime                          # When the decision was made
    decided_by: str                               # "system" for auto, user ID for human
    conditions: list[str] = []                    # Conditions for CONDITIONAL approval
    expiration_at: datetime | None = None         # When the decision expires
    validation_duration_ms: float                 # How long validation took
    # Explainability fields
    detailed_reasons: list[str] = []              # Detailed reasoning for the decision
    failed_rules: list[str] = []                  # List of rule codes that failed
    warning_rules: list[str] = []                 # List of rule codes that warned
    confidence_explanation: str = ""               # Why confidence is at this level
    suggested_fixes: list[str] = []               # Suggested remediation steps
    strategy_recommendation: str | None = None    # Planner strategy recommendation
    dependency_explanation: str = ""               # Explanation of dependency impact
    rollback_explanation: str = ""                 # Explanation of rollback feasibility
    evidence_summary: str = ""                    # Summary of evidence collected
```

### 5.3 ValidationRule

Configurable rule with conditions.

```python
class ValidationRule(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rule_id: str                                  # e.g., "SAFETY_001"
    rule_code: str                                # e.g., "SAFETY_001"
    name: str                                     # Human-readable name
    description: str                              # What this rule checks
    category: ValidationCategory                  # SAFETY, DEPENDENCY, etc.
    severity: ValidationSeverity                  # BLOCKER, WARNING, INFO
    enabled: bool = True
    conditions: list[dict[str, Any]] = []         # JSON-logic conditions
    message_on_pass: str = ""
    message_on_fail: str = ""
    suggested_fix: str = ""
    plugin_id: str | None = None                  # For plugin-provided rules
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.4 ValidationPolicy

Organizational policy with policy pack support.

```python
class ValidationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    enforcement: PolicyEnforcement                 # HARD (blocks) or SOFT (warns)
    enabled: bool = True
    conditions: list[dict[str, Any]] = []
    applicable_environments: list[str] = []       # Empty = all environments
    policy_pack_id: str | None = None             # Associated policy pack
    message_on_pass: str = ""
    message_on_fail: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.5 ValidationEvidence

Evidence tuple for audit trail.

```python
class ValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    evidence_id: str
    result_id: str
    evidence_type: str                            # "rule_result", "assessment", "external_check"
    source: str                                   # Which service produced this
    key: str                                      # What was checked
    value: Any                                    # What was found
    confidence: ConfidenceScore
    metadata: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.6 ValidationFailure

Blocker that prevents execution.

```python
class ValidationFailure(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    failure_id: str
    result_id: str
    rule_id: str
    rule_code: str
    rule_name: str
    category: ValidationCategory
    severity: ValidationSeverity
    reason: str
    suggested_fix: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.7 ValidationWarning

Non-blocking advisory.

```python
class ValidationWarning(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    warning_id: str
    result_id: str
    rule_id: str
    rule_code: str
    rule_name: str
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.8 ApprovalDecision

Human approval record.

```python
class ApprovalDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision_id: str
    request_id: str
    result_id: str | None
    plan_id: str
    decision: ApprovalStatus                      # Expanded lifecycle
    decided_by: str
    reason: str
    conditions: list[str] = []
    approval_level: ApprovalLevel
    expires_at: datetime
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.9 ExecutionPermission

Grants or denies execution.

```python
class ExecutionPermission(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    permission_id: str
    plan_id: str
    result_id: str
    granted: bool
    granted_by: str
    granted_at: datetime
    expires_at: datetime
    conditions: list[str] = []
    signature_id: str | None = None               # Link to digital signature
    revocation_reason: str | None = None
    revoked_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.10 ExecutionBlocker

Explicit execution block.

```python
class ExecutionBlocker(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    blocker_id: str
    plan_id: str
    result_id: str
    blocker_type: BlockerType
    reason: str
    rule_code: str | None = None
    policy_id: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.11 SafetyAssessment

Risk, confidence, and blast radius analysis.

```python
class SafetyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    risk_score: RiskScore
    confidence_score: ConfidenceScore
    blast_radius: int                             # Number of affected components
    historical_failures: int                      # Past failures for this pattern
    is_catastrophic: bool                         # Risk > 95
    requires_human_approval: bool
    assessment_summary: str
    factors: list[dict[str, Any]] = []
```

### 5.12 CompatibilityAssessment

Configuration, environment, and version compatibility.

```python
class CompatibilityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    config_compatible: bool
    environment_compatible: bool
    version_compatible: bool
    config_conflicts: list[str] = []
    environment_mismatches: list[str] = []
    version_incompatibilities: list[str] = []
    pre_release_components: list[str] = []
    assessment_summary: str
```

### 5.13 RollbackAssessment

Rollback feasibility analysis.

```python
class RollbackAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rollback_available: bool
    automatic_rollback: bool
    rollback_tested: bool
    rollback_success_rate: float                  # 0.0-1.0
    rollback_complexity: RollbackComplexity
    data_loss_risk: bool
    estimated_rollback_time_seconds: int
    assessment_summary: str
```

### 5.14 SimulationAssessment

Simulation results verification.

```python
class SimulationAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    simulation_performed: bool
    simulation_outcome: str                       # "success", "failure", "not_performed"
    preconditions_met: bool
    postconditions_met: bool
    simulation_duration_ms: int
    simulation_errors: list[str] = []
    assessment_summary: str
```

### 5.15 DependencyAssessment

Dependency graph and cascade analysis.

```python
class DependencyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    direct_dependencies: list[str] = []
    reverse_dependencies: list[str] = []
    blast_radius: int
    cascade_risk: CascadeRisk
    critical_path_affected: bool
    cross_boundary_impact: bool
    dependent_service_count: int
    assessment_summary: str
```

### 5.16 ResourceAssessment

Resource availability analysis.

```python
class ResourceAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cpu_available_percent: float
    memory_available_mb: float
    disk_available_gb: float
    network_impact: str                           # "none", "low", "medium", "high"
    resource_sufficient: bool
    estimated_downtime_seconds: int
    resource_conflicts: list[str] = []
    assessment_summary: str
```

### 5.17 SecurityAssessment

Security and permission analysis.

```python
class SecurityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    auth_valid: bool
    permissions_sufficient: bool
    elevated_permissions_required: bool
    audit_trail_complete: bool
    security_violations: list[str] = []
    required_roles: list[str] = []
    assessment_summary: str
```

### 5.18 CostAssessment

Cost impact analysis.

```python
class CostAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    estimated_cost_usd: float
    human_effort_hours: float
    budget_remaining_usd: float
    budget_compliant: bool
    cost_breakdown: dict[str, float] = {}
    cost_approval_required: bool
    assessment_summary: str
```

### 5.19 ValidationExplanation

Comprehensive explanation of validation results.

```python
class ValidationExplanation(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    explanation_id: str
    result_id: str
    summary: str                                 # High-level summary
    detailed_reasons: list[str]                  # Detailed reasoning
    failed_rules_explanation: str                # Why rules failed
    warning_rules_explanation: str               # Why rules warned
    confidence_explanation: str                  # Confidence reasoning
    dependency_explanation: str                  # Dependency impact explanation
    rollback_explanation: str                    # Rollback feasibility explanation
    suggested_fixes: list[str]                   # Remediation steps
    strategy_recommendation: str | None          # Recommended strategy
    evidence_summary: str                        # Evidence summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.20 ValidationSignature

Digital signature for approved plans.

```python
class ValidationSignature(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    signature_id: str
    result_id: str
    plan_id: str
    signature_hash: str                          # SHA-256 of plan + decision + timestamp
    signed_at: datetime
    signed_by: str                               # "system" for auto, user ID for human
    approval_metadata: dict[str, Any] = {}       # Approval context
    verification_method: str = "sha256"          # Hash algorithm used
    expires_at: datetime | None = None           # Signature expiry
```

### 5.21 ValidationHistoryRecord

Historical validation record for learning.

```python
class ValidationHistoryRecord(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    record_id: str
    request_id: str
    result_id: str
    plan_id: str
    incident_id: str | None
    decision: str
    risk_score: int
    confidence_score: float
    validation_duration_ms: float
    environment: str
    plan_type: str
    rules_triggered: list[str] = []              # Rule codes that fired
    was_executed: bool = False                   # Was the plan executed?
    execution_succeeded: bool | None = None      # Did execution succeed?
    is_false_positive: bool = False              # Approved but failed execution
    is_false_negative: bool = False              # Rejected but would have succeeded
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.22 ValidationStatistics

Aggregated validation statistics.

```python
class ValidationStatistics(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    stat_id: str
    period_start: datetime
    period_end: datetime
    total_validations: int
    approved_count: int
    rejected_count: int
    pending_count: int
    conditional_count: int
    average_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    approval_rate: float                         # approved / total
    false_positive_rate: float                   # false positives / approved
    false_negative_rate: float                   # false negatives / rejected
    top_failing_rules: list[dict[str, Any]] = [] # Most common failures
    computed_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.23 ValidationTrend

Historical trend data.

```python
class ValidationTrend(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    trend_id: str
    trend_type: str                              # "risk", "confidence", "failure", "approval", "latency"
    period: str                                  # "7d", "30d", "90d"
    data_points: list[dict[str, Any]] = []       # Time series data
    moving_average: float = 0.0
    trend_direction: str = "stable"              # "improving", "stable", "degrading"
    computed_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.24 ValidationCacheEntry

Cache entry for validation results.

```python
class ValidationCacheEntry(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cache_key: str                               # SHA-256 hash
    result_id: str
    plan_id: str
    environment: str
    decision: str
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
```

### 5.25 PolicyPack

Collection of policies for a specific context.

```python
class PolicyPack(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    pack_id: str
    name: str                                    # e.g., "production", "development"
    description: str
    pack_type: PolicyPackType
    enabled: bool = True
    policy_ids: list[str] = []                   # Policies in this pack
    priority: int = 0                            # Higher = evaluated first
    applicable_environments: list[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 5.26 ValidatorPlugin

Plugin metadata for extensible validation.

```python
class ValidatorPlugin(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    plugin_id: str
    name: str
    description: str
    version: str
    plugin_type: PluginType                       # INFRASTRUCTURE, CLOUD, FINANCIAL, etc.
    enabled: bool = True
    provides_rules: list[str] = []               # Rule codes this plugin provides
    provides_analyzers: list[str] = []           # Analyzer names this plugin provides
    dependencies: list[str] = []                 # Other plugin dependencies
    loaded_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 6. Value Objects

### 6.1 ConfidenceScore

```python
class ConfidenceScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: float                                  # 0.0-1.0

    @property
    def is_low(self) -> bool:
        return self.value < 0.3

    @property
    def is_medium(self) -> bool:
        return 0.3 <= self.value < 0.7

    @property
    def is_high(self) -> bool:
        return self.value >= 0.7
```

### 6.2 RiskScore

```python
class RiskScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: int                                    # 0-100

    @property
    def is_low(self) -> bool:
        return self.value < 30

    @property
    def is_medium(self) -> bool:
        return 30 <= self.value < 70

    @property
    def is_high(self) -> bool:
        return 70 <= self.value < 90

    @property
    def is_catastrophic(self) -> bool:
        return self.value >= 90
```

### 6.3 TimeRange

```python
class TimeRange(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt <= self.end
```

### 6.4 ThresholdRange

```python
class ThresholdRange(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_value: float
    max_value: float

    def contains(self, value: float) -> bool:
        return self.min_value <= value <= self.max_value
```

### 6.5 ComponentDescriptor

```python
class ComponentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    component_type: str                          # "service", "database", "cache", etc.
    environment: str
    version: str | None = None
    health_status: str | None = None
    metadata: dict[str, Any] = {}
```

### 6.6 EnvironmentDescriptor

```python
class EnvironmentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    is_production: bool
    allowed_actions: list[str] = []
    restricted_actions: list[str] = []
    required_approvals: list[str] = []
    maintenance_window: MaintenanceWindow | None = None
```

### 6.7 VersionConstraint

```python
class VersionConstraint(BaseModel):
    model_config = ConfigDict(frozen=True)

    component: str
    constraint: str                              # e.g., ">=1.0.0,<2.0.0"
    current_version: str
    required_version: str | None = None

    def is_satisfied_by(self, version: str) -> bool:
        # Version comparison logic
        ...
```

### 6.8 ResourceQuota

```python
class ResourceQuota(BaseModel):
    model_config = ConfigDict(frozen=True)

    cpu_percent: ThresholdRange
    memory_mb: float
    disk_gb: float
    network_impact: str                          # "none", "low", "medium", "high"

    @classmethod
    def production_defaults(cls) -> "ResourceQuota":
        return cls(
            cpu_percent=ThresholdRange(min_value=0, max_value=80),
            memory_mb=512,
            disk_gb=1,
            network_impact="low",
        )
```

### 6.9 MaintenanceWindow

```python
class MaintenanceWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    schedule: str                               # Cron expression
    timezone: str
    allowed_actions: list[str] = []
    blocked_actions: list[str] = []

    def is_now_in_window(self) -> bool:
        # Check if current time is within window
        ...
```

---

## 7. Enums

All enums use `StrEnum` for JSON serialization compatibility.

```python
from enum import StrEnum


class ValidationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class ValidationDecisionEnum(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    PENDING_APPROVAL = "pending_approval"
    NEEDS_REVIEW = "needs_review"
    DEFERRED = "deferred"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ValidationSeverity(StrEnum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class ValidationCategory(StrEnum):
    SAFETY = "safety"
    DEPENDENCY = "dependency"
    COMPATIBILITY = "compatibility"
    RESOURCE = "resource"
    POLICY = "policy"
    SECURITY = "security"
    ROLLBACK = "rollback"
    COST = "cost"


class ApprovalLevel(StrEnum):
    AUTO = "auto"
    DEVELOPER = "developer"
    MAINTAINER = "maintainer"
    OPERATIONS = "operations"
    ADMINISTRATOR = "administrator"
    EMERGENCY = "emergency"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    DEFERRED = "deferred"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ExecutionPermissionStatus(StrEnum):
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"


class CascadeRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RollbackComplexity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IMPOSSIBLE = "impossible"


class PolicyEnforcement(StrEnum):
    HARD = "hard"
    SOFT = "soft"


class PolicyType(StrEnum):
    APPROVAL = "approval"
    COST = "cost"
    MAINTENANCE = "maintenance"
    PRODUCTION = "production"
    SECURITY = "security"
    BUSINESS = "business"


class BlockerType(StrEnum):
    RULE_VIOLATION = "rule_violation"
    POLICY_VIOLATION = "policy_violation"
    APPROVAL_REQUIRED = "approval_required"
    SAFETY = "safety"
    RESOURCE = "resource"
    SECURITY = "security"


class PolicyPackType(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    FINANCIAL = "financial"
    PERSONAL_ASSISTANT = "personal_assistant"
    EXPERIMENTAL = "experimental"
    CUSTOM = "custom"


class PluginType(StrEnum):
    INFRASTRUCTURE = "infrastructure"
    CLOUD = "cloud"
    DATABASE = "database"
    FINANCIAL = "financial"
    CALENDAR = "calendar"
    COMMUNICATION = "communication"
    CUSTOM = "custom"


class TrendType(StrEnum):
    RISK = "risk"
    CONFIDENCE = "confidence"
    FAILURE = "failure"
    APPROVAL = "approval"
    LATENCY = "latency"
```

---

## 8. Repositories

Repository interfaces are defined as `Protocol` classes.

### 8.1 ValidationRepository

```python
class ValidationRepository(Protocol):
    async def save_result(self, result: ValidationResult) -> None: ...
    async def get_result(self, result_id: str) -> ValidationResult | None: ...
    async def list_results(
        self,
        *,
        plan_id: str | None = None,
        incident_id: str | None = None,
        status: ValidationStatus | None = None,
        decision: ValidationDecisionEnum | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ValidationResult]: ...
    async def get_by_plan(self, plan_id: str) -> ValidationResult | None: ...
    async def get_by_incident(self, incident_id: str) -> list[ValidationResult]: ...
    async def save_approval(self, approval: ApprovalDecision) -> None: ...
    async def get_pending_approvals(
        self,
        *,
        approval_level: ApprovalLevel | None = None,
        limit: int = 50,
    ) -> list[ApprovalDecision]: ...
```

### 8.2 RuleRepository

```python
class RuleRepository(Protocol):
    async def get_all_rules(self) -> list[ValidationRule]: ...
    async def get_rules_by_category(self, category: ValidationCategory) -> list[ValidationRule]: ...
    async def get_enabled_rules(self) -> list[ValidationRule]: ...
    async def get_rule_by_code(self, rule_code: str) -> ValidationRule | None: ...
    async def save_rule(self, rule: ValidationRule) -> None: ...
```

### 8.3 PolicyRepository

```python
class PolicyRepository(Protocol):
    async def get_all_policies(self) -> list[ValidationPolicy]: ...
    async def get_policies_by_type(self, policy_type: PolicyType) -> list[ValidationPolicy]: ...
    async def get_active_policies(self) -> list[ValidationPolicy]: ...
    async def get_policy_by_id(self, policy_id: str) -> ValidationPolicy | None: ...
    async def save_policy(self, policy: ValidationPolicy) -> None: ...
```

### 8.4 EvidenceRepository

```python
class EvidenceRepository(Protocol):
    async def save_evidence(self, evidence: ValidationEvidence) -> None: ...
    async def save_evidence_batch(self, evidence_list: list[ValidationEvidence]) -> None: ...
    async def get_evidence_by_result(self, result_id: str) -> list[ValidationEvidence]: ...
```

### 8.5 AuditRepository

```python
class AuditRepository(Protocol):
    async def save_audit_log(self, log: AuditLogEntry) -> None: ...
    async def get_audit_logs(
        self,
        *,
        plan_id: str | None = None,
        result_id: str | None = None,
        action: str | None = None,
        actor: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]: ...
```

### 8.6 ValidationHistoryRepository

```python
class ValidationHistoryRepository(Protocol):
    async def save_history(self, record: ValidationHistoryRecord) -> None: ...
    async def get_history_by_plan(self, plan_id: str) -> list[ValidationHistoryRecord]: ...
    async def get_history_by_incident(self, incident_id: str) -> list[ValidationHistoryRecord]: ...
    async def get_statistics(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        environment: str | None = None,
    ) -> ValidationStatistics: ...
    async def get_false_positives(self, limit: int = 100) -> list[ValidationHistoryRecord]: ...
    async def get_false_negatives(self, limit: int = 100) -> list[ValidationHistoryRecord]: ...
    async def get_recurring_failures(
        self,
        *,
        rule_code: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...
```

### 8.7 SignatureRepository

```python
class SignatureRepository(Protocol):
    async def save_signature(self, signature: ValidationSignature) -> None: ...
    async def get_signature_by_plan(self, plan_id: str) -> ValidationSignature | None: ...
    async def get_signature_by_result(self, result_id: str) -> ValidationSignature | None: ...
    async def verify_signature(self, plan_id: str, plan_hash: str) -> bool: ...
```

### 8.8 PolicyPackRepository

```python
class PolicyPackRepository(Protocol):
    async def get_all_packs(self) -> list[PolicyPack]: ...
    async def get_pack_by_id(self, pack_id: str) -> PolicyPack | None: ...
    async def get_packs_by_type(self, pack_type: PolicyPackType) -> list[PolicyPack]: ...
    async def get_active_packs(self) -> list[PolicyPack]: ...
    async def save_pack(self, pack: PolicyPack) -> None: ...
```

### 8.9 PluginRepository

```python
class PluginRepository(Protocol):
    async def get_all_plugins(self) -> list[ValidatorPlugin]: ...
    async def get_plugin_by_id(self, plugin_id: str) -> ValidatorPlugin | None: ...
    async def get_enabled_plugins(self) -> list[ValidatorPlugin]: ...
    async def save_plugin(self, plugin: ValidatorPlugin) -> None: ...
    async def disable_plugin(self, plugin_id: str) -> None: ...
```

---

## 9. Services

### 9.1 Service Overview

| Service | Location | Responsibility |
|---------|----------|---------------|
| ValidationService | `application/services/validation_service.py` | Orchestrator. Pipeline execution. |
| RuleEngine | `application/services/rule_engine.py` | Evaluates rules, produces blockers/warnings. |
| PolicyEngine | `application/services/policy_engine.py` | Evaluates policies, enforces hard/soft. |
| ApprovalEngine | `application/services/approval_engine.py` | Determines approval level, manages workflow. |
| DependencyAnalyzer | `application/services/dependency_analyzer.py` | Graph traversal, blast radius calculation. |
| CompatibilityAnalyzer | `application/services/compatibility_analyzer.py` | Config, env, version checks. |
| RollbackAnalyzer | `application/services/rollback_analyzer.py` | Rollback feasibility assessment. |
| SecurityAnalyzer | `application/services/security_analyzer.py` | Permission, auth, audit checks. |
| SimulationVerifier | `application/services/simulation_verifier.py` | Validates simulation results. |
| EnvironmentAnalyzer | `application/services/environment_analyzer.py` | Environment-specific constraints. |
| ResourceAnalyzer | `application/services/resource_analyzer.py` | CPU, memory, disk, network checks. |
| DecisionEngine | `application/services/decision_engine.py` | Aggregates assessments, makes final decision. |
| SummaryGenerator | `application/services/summary_generator.py` | Human-readable validation summary. |
| ExplainabilityService | `application/services/explainability_service.py` | Generates detailed explanations. |
| ValidationHistoryService | `application/services/history_service.py` | Stores and queries validation history. |
| TrendAnalysisService | `application/services/trend_service.py` | Computes validation trends. |
| ValidationCacheService | `application/services/cache_service.py` | Caches validation results. |
| PluginManager | `infrastructure/plugins/plugin_manager.py` | Discovers and loads plugins. |
| PolicyPackLoader | `application/services/policy_pack_loader.py` | Loads and selects policy packs. |

### 9.2 ValidationService

The orchestrator. Receives a request, runs the pipeline, produces a decision.

```python
class ValidationService:
    def __init__(
        self,
        *,
        rule_engine: RuleEngine,
        policy_engine: PolicyEngine,
        approval_engine: ApprovalEngine,
        dependency_analyzer: DependencyAnalyzer,
        compatibility_analyzer: CompatibilityAnalyzer,
        rollback_analyzer: RollbackAnalyzer,
        security_analyzer: SecurityAnalyzer,
        simulation_verifier: SimulationVerifier,
        environment_analyzer: EnvironmentAnalyzer,
        resource_analyzer: ResourceAnalyzer,
        decision_engine: DecisionEngine,
        summary_generator: SummaryGenerator,
        explainability_service: ExplainabilityService,
        history_service: ValidationHistoryService,
        cache_service: ValidationCacheService,
        validation_repository: ValidationRepository,
        evidence_repository: EvidenceRepository,
        audit_repository: AuditRepository,
        event_publisher: EventPublisher,
    ) -> None: ...

    async def validate(self, request: ValidationRequest) -> ValidationDecision:
        """Run the validation pipeline with caching."""
        # Check cache first
        cached = await self._cache_service.get(request)
        if cached:
            return cached

        # Run pipeline
        decision = await self._run_pipeline(request)

        # Store in cache
        await self._cache_service.put(request, decision)

        # Store history
        await self._history_service.record(request, decision)

        return decision

    async def approve(
        self,
        request_id: str,
        decided_by: str,
        reason: str,
        conditions: list[str] | None = None,
    ) -> ApprovalDecision: ...

    async def reject(
        self,
        request_id: str,
        decided_by: str,
        reason: str,
    ) -> ApprovalDecision: ...
```

### 9.3 RuleEngine

```python
class RuleEngine:
    def __init__(
        self,
        *,
        rule_repository: RuleRepository,
        cache: RulePolicyCache,
        plugin_manager: PluginManager,
    ) -> None: ...

    async def evaluate(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
    ) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
        """Evaluate all enabled rules including plugin rules."""
        ...
```

### 9.4 PolicyEngine

```python
class PolicyEngine:
    def __init__(
        self,
        *,
        policy_repository: PolicyRepository,
        policy_pack_loader: PolicyPackLoader,
        cache: RulePolicyCache,
    ) -> None: ...

    async def evaluate(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
    ) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
        """Evaluate all active policies from selected policy pack."""
        ...
```

### 9.5 ApprovalEngine

```python
class ApprovalEngine:
    def __init__(
        self,
        *,
        validation_repository: ValidationRepository,
    ) -> None: ...

    def determine_approval_level(
        self,
        risk_score: RiskScore,
        environment: str,
        severity: str,
        confidence: ConfidenceScore,
        rollback_available: bool,
    ) -> ApprovalLevel: ...

    async def check_approval_status(
        self,
        request_id: str,
        required_level: ApprovalLevel,
    ) -> ApprovalDecision | None: ...

    async def escalate(
        self,
        current_level: ApprovalLevel,
        request_id: str,
    ) -> ApprovalLevel: ...
```

### 9.6 ExplainabilityService

Generates detailed explanations for validation decisions.

```python
class ExplainabilityService:
    async def generate_explanation(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
        failures: list[ValidationFailure],
        warnings: list[ValidationWarning],
        decision: ValidationDecision,
    ) -> ValidationExplanation:
        """Generate comprehensive explanation for the validation result."""
        ...

    async def explain_rule_failure(
        self,
        failure: ValidationFailure,
        context: dict[str, Any],
    ) -> str:
        """Explain why a specific rule failed."""
        ...

    async def explain_decision(
        self,
        decision: ValidationDecision,
        assessments: dict[str, Any],
    ) -> str:
        """Explain the overall decision rationale."""
        ...
```

### 9.7 ValidationHistoryService

Stores and queries validation history for learning.

```python
class ValidationHistoryService:
    def __init__(
        self,
        *,
        history_repository: ValidationHistoryRepository,
    ) -> None: ...

    async def record(
        self,
        request: ValidationRequest,
        decision: ValidationDecision,
    ) -> None:
        """Record a validation result for history."""
        ...

    async def record_execution_outcome(
        self,
        plan_id: str,
        succeeded: bool,
    ) -> None:
        """Record whether an executed plan succeeded or failed."""
        ...

    async def get_statistics(
        self,
        *,
        period_start: datetime,
        period_end: datetime,
        environment: str | None = None,
    ) -> ValidationStatistics:
        """Get aggregated validation statistics."""
        ...

    async def get_false_positives(self, limit: int = 100) -> list[ValidationHistoryRecord]:
        """Get approved plans that failed execution."""
        ...

    async def get_false_negatives(self, limit: int = 100) -> list[ValidationHistoryRecord]:
        """Get rejected plans that would have succeeded."""
        ...

    async def get_recurring_failures(
        self,
        *,
        rule_code: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get rules that fail repeatedly."""
        ...

    async def predict_outcome(
        self,
        request: ValidationRequest,
    ) -> dict[str, Any]:
        """Predict validation outcome based on historical patterns."""
        ...
```

### 9.8 TrendAnalysisService

Computes historical validation trends.

```python
class TrendAnalysisService:
    def __init__(
        self,
        *,
        history_repository: ValidationHistoryRepository,
    ) -> None: ...

    async def compute_risk_trend(
        self,
        *,
        period: str = "7d",
        environment: str | None = None,
    ) -> ValidationTrend: ...

    async def compute_confidence_trend(
        self,
        *,
        period: str = "7d",
        environment: str | None = None,
    ) -> ValidationTrend: ...

    async def compute_failure_trend(
        self,
        *,
        period: str = "7d",
        environment: str | None = None,
    ) -> ValidationTrend: ...

    async def compute_approval_trend(
        self,
        *,
        period: str = "7d",
        environment: str | None = None,
    ) -> ValidationTrend: ...

    async def compute_latency_trend(
        self,
        *,
        period: str = "7d",
        environment: str | None = None,
    ) -> ValidationTrend: ...
```

### 9.9 ValidationCacheService

Caches validation results for identical plans.

```python
class ValidationCacheService:
    def __init__(
        self,
        *,
        cache_backend: ValidationCacheBackend,
        ttl_seconds: int = 300,
        max_entries: int = 10000,
    ) -> None: ...

    def _compute_cache_key(
        self,
        request: ValidationRequest,
        rules_version: str,
        policies_version: str,
    ) -> str:
        """Compute SHA-256 cache key from plan + environment + versions."""
        ...

    async def get(
        self,
        request: ValidationRequest,
    ) -> ValidationDecision | None:
        """Get cached validation result if available."""
        ...

    async def put(
        self,
        request: ValidationRequest,
        decision: ValidationDecision,
    ) -> None:
        """Store validation result in cache."""
        ...

    async def invalidate(
        self,
        *,
        plan_id: str | None = None,
        environment: str | None = None,
    ) -> int:
        """Invalidate cache entries. Returns count of invalidated entries."""
        ...

    async def clear(self) -> None:
        """Clear all cache entries."""
        ...
```

### 9.10 DependencyAnalyzer

```python
class DependencyAnalyzer:
    def __init__(
        self,
        *,
        service_registry: ServiceRegistry,
    ) -> None: ...

    async def analyze(
        self,
        request: ValidationRequest,
    ) -> DependencyAssessment: ...

    def _calculate_blast_radius(
        self,
        affected_components: list[str],
        dependency_graph: dict[str, list[str]],
    ) -> int: ...

    def _assess_cascade_risk(
        self,
        blast_radius: int,
        critical_path_affected: bool,
        dependent_count: int,
    ) -> CascadeRisk: ...
```

### 9.11 CompatibilityAnalyzer

```python
class CompatibilityAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> CompatibilityAssessment: ...

    async def check_config_compatibility(
        self,
        plan: dict[str, Any],
        environment: str,
    ) -> tuple[bool, list[str]]: ...

    async def check_version_compatibility(
        self,
        plan: dict[str, Any],
    ) -> tuple[bool, list[str]]: ...
```

### 9.12 RollbackAnalyzer

```python
class RollbackAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> RollbackAssessment: ...
```

### 9.13 SecurityAnalyzer

```python
class SecurityAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> SecurityAssessment: ...
```

### 9.14 SimulationVerifier

```python
class SimulationVerifier:
    async def verify(
        self,
        request: ValidationRequest,
    ) -> SimulationAssessment: ...
```

### 9.15 EnvironmentAnalyzer

```python
class EnvironmentAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> SafetyAssessment: ...
```

### 9.16 ResourceAnalyzer

```python
class ResourceAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> ResourceAssessment: ...
```

### 9.17 DecisionEngine

```python
class DecisionEngine:
    async def decide(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
        failures: list[ValidationFailure],
        warnings: list[ValidationWarning],
    ) -> ValidationDecision: ...
```

### 9.18 SummaryGenerator

```python
class SummaryGenerator:
    async def generate(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
        failures: list[ValidationFailure],
        warnings: list[ValidationWarning],
        decision: ValidationDecision,
    ) -> str: ...
```

### 9.19 PolicyPackLoader

Loads and selects appropriate policy packs.

```python
class PolicyPackLoader:
    def __init__(
        self,
        *,
        policy_pack_repository: PolicyPackRepository,
    ) -> None: ...

    async def select_pack(
        self,
        request: ValidationRequest,
    ) -> PolicyPack:
        """Select the appropriate policy pack for this request."""
        ...

    async def load_policies(
        self,
        pack: PolicyPack,
    ) -> list[ValidationPolicy]:
        """Load all policies from a pack."""
        ...
```

### 9.20 PluginManager

Discovers, loads, and manages validator plugins.

```python
class PluginManager:
    def __init__(
        self,
        *,
        plugin_repository: PluginRepository,
    ) -> None: ...

    async def discover_plugins(self) -> list[ValidatorPlugin]:
        """Discover available plugins."""
        ...

    async def load_plugin(
        self,
        plugin_id: str,
    ) -> ValidatorPlugin:
        """Load a specific plugin."""
        ...

    async def get_plugin_rules(
        self,
        plugin_id: str,
    ) -> list[ValidationRule]:
        """Get rules provided by a plugin."""
        ...

    async def get_plugin_analyzers(
        self,
        plugin_id: str,
    ) -> list[str]:
        """Get analyzers provided by a plugin."""
        ...

    async def reload_plugins(self) -> None:
        """Reload all enabled plugins."""
        ...
```

---

## 10. Validation Rules

### 10.1 Safety Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| SAFETY_001 | Block Database Restart During Migration | BLOCKER | Never restart database if active migration running |
| SAFETY_002 | Block Redis Restart During Cache Migration | BLOCKER | Never restart Redis during active cache migration |
| SAFETY_003 | Block Production Data Deletion | BLOCKER | Never delete production data |
| SAFETY_004 | Block Deploy If Tests Failed | BLOCKER | Never deploy if tests failed |
| SAFETY_005 | Block Low-Confidence Repair in Production | BLOCKER | Never execute low-confidence repair (<0.3) in production |
| SAFETY_006 | Block Restart Without Rollback Plan | BLOCKER | Never restart service without rollback plan |
| SAFETY_007 | Block Catastrophic Risk Repairs | BLOCKER | Block catastrophic risk (>90) repairs |
| SAFETY_008 | Block Multi-Component Repairs | BLOCKER | Block repairs affecting more than 5 components |

### 10.2 Dependency Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| DEPENDENCY_001 | Block Critical Path Service Impact | BLOCKER | Block if critical path service affected |
| DEPENDENCY_002 | Block Critical Cascade Risk | BLOCKER | Block if cascade risk is CRITICAL |
| DEPENDENCY_003 | Require Staging Validation | WARNING | Require staging validation if >3 components affected |
| DEPENDENCY_004 | Block Cross-Boundary Impact | BLOCKER | Block if cross-boundary impact detected |
| DEPENDENCY_005 | Require Rollback for High-Dep Services | BLOCKER | Require rollback for services with >100 dependents |

### 10.3 Compatibility Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| COMPAT_001 | Block Configuration Conflict | BLOCKER | Block if configuration conflict detected |
| COMPAT_002 | Block Environment Mismatch | BLOCKER | Block if environment mismatch |
| COMPAT_003 | Block Version Incompatibility | BLOCKER | Block if version incompatibility detected |
| COMPAT_004 | Require Manual Review for Pre-Release | WARNING | Require manual review for pre-release versions |
| COMPAT_005 | Block Dependency Version Constraint Violation | BLOCKER | Block if dependency version constraint violated |

### 10.4 Resource Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| RESOURCE_001 | Block Low CPU | BLOCKER | Block if CPU availability <20% |
| RESOURCE_002 | Block Low Memory | BLOCKER | Block if memory availability <512MB |
| RESOURCE_003 | Block Low Disk | BLOCKER | Block if disk space <1GB |
| RESOURCE_004 | Block High Network Impact | BLOCKER | Block if network impact is HIGH during peak hours |
| RESOURCE_005 | Block Excessive Downtime | BLOCKER | Block if estimated downtime >maintenance window |

### 10.5 Policy Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| POLICY_001 | Production Changes Require Approval | BLOCKER | Production changes require maintainer approval |
| POLICY_002 | Critical Severity Requires Admin | BLOCKER | Critical severity requires administrator approval |
| POLICY_003 | Outside Maintenance Window | BLOCKER | Operations outside maintenance window blocked |
| POLICY_004 | Cost Exceeds Budget | BLOCKER | Cost impact >budget threshold requires approval |
| POLICY_005 | Emergency Override Requires Role | BLOCKER | Emergency override requires emergency role |
| POLICY_006 | Database Changes Require DBA | BLOCKER | Database changes require DBA approval |
| POLICY_007 | Redis Changes Require Cache Team | BLOCKER | Redis changes require cache team approval |
| POLICY_008 | Network Changes Require Network Team | BLOCKER | Network changes require network team approval |

### 10.6 Security Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| SECURITY_001 | Block Expired Auth Token | BLOCKER | Block if auth token expired |
| SECURITY_002 | Block Insufficient Role | BLOCKER | Block if user lacks required role |
| SECURITY_003 | Block Elevated Permissions | BLOCKER | Block if action requires elevated permissions |
| SECURITY_004 | Block Incomplete Audit Trail | BLOCKER | Block if audit trail incomplete |

### 10.7 Rollback Rules

| Code | Name | Severity | Description |
|------|------|----------|-------------|
| ROLLBACK_001 | Block No Rollback with Risk | BLOCKER | Block if rollback not available and risk >medium |
| ROLLBACK_002 | Block Impossible Rollback | BLOCKER | Block if rollback complexity is IMPOSSIBLE |
| ROLLBACK_003 | Warn Low Rollback Success | WARNING | Warn if rollback success rate <80% |
| ROLLBACK_004 | Block Data Loss Risk | BLOCKER | Block if data loss risk detected during rollback |

---

## 11. Approval Policy

### 11.1 Approval Hierarchy

```
Level 6: EMERGENCY    ── Any env, emergency override with full audit
Level 5: ADMINISTRATOR ── Production, risk >= 90, or catastrophic severity
Level 4: OPERATIONS    ── Production, risk < 90, or critical severity
Level 3: MAINTAINER    ── Production, risk < 70
Level 2: DEVELOPER     ── Any env, risk < 50, confidence > 0.6
Level 1: AUTO          ── Dev/staging only, risk < 30, confidence > 0.8, rollback available
```

### 11.2 Approval Level Determination

```python
def determine_approval_level(
    risk_score: RiskScore,
    environment: str,
    severity: str,
    confidence: ConfidenceScore,
    rollback_available: bool,
) -> ApprovalLevel:
    is_production = environment == "production"

    if (
        not is_production
        and risk_score.value < 30
        and confidence.value > 0.8
        and rollback_available
    ):
        return ApprovalLevel.AUTO

    if risk_score.value < 50 and confidence.value > 0.6:
        return ApprovalLevel.DEVELOPER

    if is_production and risk_score.value < 70:
        return ApprovalLevel.MAINTAINER

    if is_production and (risk_score.value < 90 or severity == "critical"):
        return ApprovalLevel.OPERATIONS

    return ApprovalLevel.ADMINISTRATOR
```

### 11.3 Escalation Matrix

| Current Level | Escalates To | Trigger |
|---------------|-------------|---------|
| AUTO | DEVELOPER | Risk increases or confidence drops |
| DEVELOPER | MAINTAINER | Environment is production OR risk >= 50 |
| MAINTAINER | OPERATIONS | Risk >= 70 OR severity is critical |
| OPERATIONS | ADMINISTRATOR | Risk >= 90 OR severity is catastrophic |
| ADMINISTRATOR | EMERGENCY | System-wide incident OR emergency override |

### 11.4 Timeout Rules

| Context | Timeout | Action on Timeout |
|---------|---------|------------------|
| Default (any level) | 24 hours | Auto-escalate to next level |
| Production environment | 4 hours | Auto-escalate to next level |
| Critical severity | 1 hour | Auto-escalate to next level |
| Emergency override | 30 minutes | Auto-expire, full audit |

### 11.5 Delegation Rules

- **AUTO**: No delegation needed (system-authorized)
- **DEVELOPER**: Can be delegated to any user with `developer` role
- **MAINTAINER**: Can be delegated to any user with `maintainer` role OR higher
- **OPERATIONS**: Can be delegated to any user with `operations` role OR higher
- **ADMINISTRATOR**: Cannot be delegated (must be explicit approval)
- **EMERGENCY**: Cannot be delegated (must be explicit approval with audit)

### 11.6 Conditional Approval

Conditional approvals attach conditions that must be met before execution:

```python
conditions = [
    "monitor_cpu_during_execution",
    "rollback_plan_must_be_tested",
    "notify_operations_channel",
    "execute_during_maintenance_window_only",
]
```

### 11.7 Approval State Transitions

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ APPROVED │    │ REJECTED │    │ CANCELLED│
    └──────────┘    └──────────┘    └──────────┘
            │
            ▼
    ┌──────────────┐
    │  CONDITIONAL │
    └──────┬───────┘
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
┌───────┐ ┌───────┐ ┌─────────┐
│DEFERRED│ │TIMED  │ │ESCALATED│
└───────┘ │  OUT  │ └─────────┘
          └───────┘

Other transitions:
- PENDING → NEEDS_REVIEW (manual intervention required)
- Any → EXPIRED (timeout exceeded)
- Any → ESCALATED (escalation triggered)
```

---

## 12. Validation Pipeline

### 12.1 Pipeline Overview

The Validation Pipeline is a sequential pipeline with optional AI validation. Each stage produces evidence and assessments. The pipeline halts early if a BLOCKER failure is detected.

```
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION PIPELINE                          │
│                                                                 │
│  Stage 1:  Input Normalization                                  │
│      │                                                          │
│      ▼                                                          │
│  Stage 2:  Evidence Collection                                  │
│      │                                                          │
│      ▼                                                          │
│  Stage 3:  Safety Assessment                                    │
│      │                                                          │
│      ▼                                                          │
│  Stage 4:  Dependency Assessment                                │
│      │                                                          │
│      ▼                                                          │
│  Stage 5:  Compatibility Assessment                             │
│      │                                                          │
│      ▼                                                          │
│  Stage 6:  Rollback Assessment                                  │
│      │                                                          │
│      ▼                                                          │
│  Stage 7:  Simulation Assessment                                │
│      │                                                          │
│      ▼                                                          │
│  Stage 8:  Resource Assessment                                  │
│      │                                                          │
│      ▼                                                          │
│  Stage 9:  Security Assessment                                  │
│      │                                                          │
│      ▼                                                          │
│  Stage 10: Rule Engine                                          │
│      │                                                          │
│      ▼                                                          │
│  Stage 11: Policy Engine                                        │
│      │                                                          │
│      ▼                                                          │
│  Stage 12: AI Validator (Optional)                              │
│      │                                                          │
│      ▼                                                          │
│  Stage 13: Decision Engine                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Stage Descriptions

| Stage | Input | Output | Service |
|-------|-------|--------|---------|
| 1. Input Normalization | Raw request | `ValidationRequest` | ValidationService |
| 2. Evidence Collection | `ValidationRequest` | `list[ValidationEvidence]` | EvidenceRepository |
| 3. Safety Assessment | Request + Evidence | `SafetyAssessment` | EnvironmentAnalyzer |
| 4. Dependency Assessment | Request + Safety | `DependencyAssessment` | DependencyAnalyzer |
| 5. Compatibility Assessment | Request | `CompatibilityAssessment` | CompatibilityAnalyzer |
| 6. Rollback Assessment | Request | `RollbackAssessment` | RollbackAnalyzer |
| 7. Simulation Assessment | Request | `SimulationAssessment` | SimulationVerifier |
| 8. Resource Assessment | Request | `ResourceAssessment` | ResourceAnalyzer |
| 9. Security Assessment | Request | `SecurityAssessment` | SecurityAnalyzer |
| 10. Rule Engine | All assessments | `failures` + `warnings` | RuleEngine |
| 11. Policy Engine | All assessments | `failures` + `warnings` | PolicyEngine |
| 12. AI Validator | All assessments | `AIValidationResult` | AIValidator (optional) |
| 13. Decision Engine | All assessments + failures + warnings | `ValidationDecision` | DecisionEngine |

### 12.3 Happy Path (Auto-Approved)

```
Planner                  Validation Engine              Execution Engine
   │                           │                              │
   │  PlanGenerated            │                              │
   │──────────────────────────▶│                              │
   │                           │                              │
   │                           │ ┌─ Stage 1: Normalize       │
   │                           │ ├─ Stage 2: Evidence        │
   │                           │ ├─ Stage 3: Safety OK       │
   │                           │ ├─ Stage 4: Dependencies OK │
   │                           │ ├─ Stage 5: Compatible OK   │
   │                           │ ├─ Stage 6: Rollback OK     │
   │                           │ ├─ Stage 7: Simulation OK   │
   │                           │ ├─ Stage 8: Resources OK    │
   │                           │ ├─ Stage 9: Security OK     │
   │                           │ ├─ Stage 10: Rules PASS     │
   │                           │ ├─ Stage 11: Policies PASS  │
   │                           │ ├─ Stage 12: AI OK          │
   │                           │ └─ Stage 13: DECIDE         │
   │                           │                              │
   │                           │ Decision: APPROVED          │
   │                           │ Permission: GRANTED         │
   │                           │ Signature: CREATED          │
   │                           │                              │
   │  ValidationCompleted      │                              │
   │  (APPROVED)               │                              │
   │◀──────────────────────────│                              │
   │                           │                              │
   │                           │  ValidationPermissionGranted │
   │                           │─────────────────────────────▶│
   │                           │                              │
   │                           │                              │ Execute
```

### 12.4 Requires Approval Path

```
Planner                  Validation Engine              Human Approver
   │                           │                              │
   │  PlanGenerated            │                              │
   │──────────────────────────▶│                              │
   │                           │                              │
   │                           │ ┌─ Run pipeline             │
   │                           │ └─ DECIDE                   │
   │                           │                              │
   │                           │ Decision: PENDING_APPROVAL  │
   │                           │ Approval Level: MAINTAINER  │
   │                           │                              │
   │  ValidationApprovalRequired│                              │
   │◀──────────────────────────│                              │
   │                           │                              │
   │                           │  Notify approver            │
   │                           │─────────────────────────────▶│
   │                           │                              │
   │                           │                              │ Review
   │                           │                              │ Approve
   │                           │                              │
   │                           │  ApprovalDecision           │
   │                           │◀─────────────────────────────│
   │                           │                              │
   │                           │ Permission: GRANTED         │
   │                           │ Signature: CREATED          │
   │                           │                              │
   │  ValidationCompleted      │                              │
   │  (APPROVED)               │                              │
   │◀──────────────────────────│                              │
```

### 12.5 Rejected Path

```
Planner                  Validation Engine
   │                           │
   │  PlanGenerated            │
   │──────────────────────────▶│
   │                           │
   │                           │ ┌─ Run pipeline
   │                           │ ├─ SAFETY_001 BLOCKER
   │                           │ └─ DECIDE
   │                           │
   │                           │ Decision: REJECTED
   │                           │ Failure: SAFETY_001
   │                           │ Explanation: ...
   │                           │
   │  ValidationCompleted      │
   │  (REJECTED)               │
   │◀──────────────────────────│
```

### 12.6 Conditional Approval Path

```
Planner                  Validation Engine              Human Approver
   │                           │                              │
   │  PlanGenerated            │                              │
   │──────────────────────────▶│                              │
   │                           │                              │
   │                           │ ┌─ Run pipeline             │
   │                           │ └─ DECIDE                   │
   │                           │                              │
   │                           │ Decision: CONDITIONAL       │
   │                           │ Conditions: [...]           │
   │                           │                              │
   │  ValidationApprovalRequired│                              │
   │◀──────────────────────────│                              │
   │                           │                              │
   │                           │                              │ Approve with conditions
   │                           │                              │
   │                           │  ApprovalDecision           │
   │                           │◀─────────────────────────────│
   │                           │                              │
   │                           │ Permission: GRANTED         │
   │                           │ Conditions: [...]           │
   │                           │                              │
   │  ValidationCompleted      │                              │
   │  (CONDITIONAL)            │                              │
   │◀──────────────────────────│                              │
```

---

## 13. Database

### 13.1 Schema Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      UAES Tables                                 │
│                                                                  │
│  uaes_validation_requests ──┬── uaes_validation_results          │
│                             │       │                            │
│                             │       ├── uaes_validation_failures │
│                             │       ├── uaes_validation_warnings │
│                             │       ├── uaes_validation_evidence │
│                             │       └── uaes_execution_permissions│
│                             │                                    │
│                             ├── uaes_approval_decisions          │
│                             │                                    │
│                             ├── uaes_validation_signatures       │
│                             │                                    │
│                             ├── uaes_validation_history          │
│                             │                                    │
│                             ├── uaes_policy_packs                │
│                             │                                    │
│                             ├── uaes_validator_plugins           │
│                             │                                    │
│                             └── uaes_validation_audit_log        │
└─────────────────────────────────────────────────────────────────┘
```

### 13.2 Tables

#### uaes_validation_requests

```sql
CREATE TABLE uaes_validation_requests (
    request_id          VARCHAR(36) PRIMARY KEY,
    plan_id             VARCHAR(36) NOT NULL,
    incident_id         VARCHAR(36),
    request_json        TEXT NOT NULL,
    plan_type           VARCHAR(50) NOT NULL DEFAULT 'infrastructure_repair',
    environment         VARCHAR(50) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvr_plan_id ON uaes_validation_requests(plan_id);
CREATE INDEX idx_uvr_incident_id ON uaes_validation_requests(incident_id);
CREATE INDEX idx_uvr_status ON uaes_validation_requests(status);
CREATE INDEX idx_uvr_created_at ON uaes_validation_requests(created_at);
```

#### uaes_validation_results

```sql
CREATE TABLE uaes_validation_results (
    result_id               VARCHAR(36) PRIMARY KEY,
    request_id              VARCHAR(36) NOT NULL REFERENCES uaes_validation_requests(request_id),
    plan_id                 VARCHAR(36) NOT NULL,
    incident_id             VARCHAR(36),
    decision                VARCHAR(30) NOT NULL,
    decision_reason         TEXT NOT NULL,
    summary_json            TEXT NOT NULL,
    explanation_json        TEXT,                          -- NEW: Explainability
    rules_evaluated         INTEGER NOT NULL DEFAULT 0,
    rules_passed            INTEGER NOT NULL DEFAULT 0,
    rules_failed            INTEGER NOT NULL DEFAULT 0,
    approval_required       BOOLEAN NOT NULL DEFAULT FALSE,
    approval_level          VARCHAR(30),
    signature_id            VARCHAR(36),                   -- NEW: Digital signature
    validated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validation_duration_ms  FLOAT NOT NULL DEFAULT 0,
    cache_key               VARCHAR(64),                   -- NEW: Cache key
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvr_result_plan_id ON uaes_validation_results(plan_id);
CREATE INDEX idx_uvr_result_incident_id ON uaes_validation_results(incident_id);
CREATE INDEX idx_uvr_result_decision ON uaes_validation_results(decision);
CREATE INDEX idx_uvr_result_validated_at ON uaes_validation_results(validated_at);
CREATE INDEX idx_uvr_result_cache_key ON uaes_validation_results(cache_key);
```

#### uaes_validation_failures

```sql
CREATE TABLE uaes_validation_failures (
    failure_id      VARCHAR(36) PRIMARY KEY,
    result_id       VARCHAR(36) NOT NULL REFERENCES uaes_validation_results(result_id),
    rule_id         VARCHAR(36) NOT NULL,
    rule_code       VARCHAR(50) NOT NULL,
    rule_name       VARCHAR(255) NOT NULL,
    category        VARCHAR(30) NOT NULL,
    severity        VARCHAR(20) NOT NULL,
    reason          TEXT NOT NULL,
    suggested_fix   TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvfl_result_id ON uaes_validation_failures(result_id);
CREATE INDEX idx_uvfl_rule_code ON uaes_validation_failures(rule_code);
```

#### uaes_validation_warnings

```sql
CREATE TABLE uaes_validation_warnings (
    warning_id      VARCHAR(36) PRIMARY KEY,
    result_id       VARCHAR(36) NOT NULL REFERENCES uaes_validation_results(result_id),
    rule_id         VARCHAR(36) NOT NULL,
    rule_code       VARCHAR(50) NOT NULL,
    rule_name       VARCHAR(255) NOT NULL,
    category        VARCHAR(30) NOT NULL,
    severity        VARCHAR(20) NOT NULL,
    message         TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvw_result_id ON uaes_validation_warnings(result_id);
CREATE INDEX idx_uvw_rule_code ON uaes_validation_warnings(rule_code);
```

#### uaes_validation_evidence

```sql
CREATE TABLE uaes_validation_evidence (
    evidence_id     VARCHAR(36) PRIMARY KEY,
    result_id       VARCHAR(36) NOT NULL REFERENCES uaes_validation_results(result_id),
    evidence_type   VARCHAR(50) NOT NULL,
    source          VARCHAR(100) NOT NULL,
    key             VARCHAR(100) NOT NULL,
    value_json      TEXT NOT NULL,
    confidence      FLOAT NOT NULL DEFAULT 0.0,
    metadata_json   TEXT NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uve_result_id ON uaes_validation_evidence(result_id);
CREATE INDEX idx_uve_source ON uaes_validation_evidence(source);
```

#### uaes_approval_decisions

```sql
CREATE TABLE uaes_approval_decisions (
    decision_id         VARCHAR(36) PRIMARY KEY,
    request_id          VARCHAR(36) NOT NULL REFERENCES uaes_validation_requests(request_id),
    result_id           VARCHAR(36) REFERENCES uaes_validation_results(result_id),
    plan_id             VARCHAR(36) NOT NULL,
    decision            VARCHAR(30) NOT NULL,
    decided_by          VARCHAR(100) NOT NULL,
    reason              TEXT NOT NULL DEFAULT '',
    conditions_json     TEXT NOT NULL DEFAULT '[]',
    approval_level      VARCHAR(30) NOT NULL,
    expires_at          TIMESTAMPTZ NOT NULL,
    decided_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uad_request_id ON uaes_approval_decisions(request_id);
CREATE INDEX idx_uad_plan_id ON uaes_approval_decisions(plan_id);
CREATE INDEX idx_uad_decision ON uaes_approval_decisions(decision);
CREATE INDEX idx_uad_decided_by ON uaes_approval_decisions(decided_by);
```

#### uaes_execution_permissions

```sql
CREATE TABLE uaes_execution_permissions (
    permission_id       VARCHAR(36) PRIMARY KEY,
    plan_id             VARCHAR(36) NOT NULL,
    result_id           VARCHAR(36) NOT NULL REFERENCES uaes_validation_results(result_id),
    granted             BOOLEAN NOT NULL DEFAULT FALSE,
    granted_by          VARCHAR(100) NOT NULL,
    granted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,
    conditions_json     TEXT NOT NULL DEFAULT '[]',
    signature_id        VARCHAR(36),                       -- NEW: Link to signature
    revocation_reason   TEXT,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uep_plan_id ON uaes_execution_permissions(plan_id);
CREATE INDEX idx_uep_granted ON uaes_execution_permissions(granted);
CREATE INDEX idx_uep_expires_at ON uaes_execution_permissions(expires_at);
```

#### uaes_validation_signatures (NEW)

```sql
CREATE TABLE uaes_validation_signatures (
    signature_id        VARCHAR(36) PRIMARY KEY,
    result_id           VARCHAR(36) NOT NULL REFERENCES uaes_validation_results(result_id),
    plan_id             VARCHAR(36) NOT NULL,
    signature_hash      VARCHAR(64) NOT NULL,             -- SHA-256
    signed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    signed_by           VARCHAR(100) NOT NULL,
    approval_metadata   TEXT NOT NULL DEFAULT '{}',
    verification_method VARCHAR(50) NOT NULL DEFAULT 'sha256',
    expires_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvs_plan_id ON uaes_validation_signatures(plan_id);
CREATE INDEX idx_uvs_result_id ON uaes_validation_signatures(result_id);
CREATE INDEX idx_uvs_signature_hash ON uaes_validation_signatures(signature_hash);
```

#### uaes_validation_history (NEW)

```sql
CREATE TABLE uaes_validation_history (
    record_id           VARCHAR(36) PRIMARY KEY,
    request_id          VARCHAR(36) NOT NULL,
    result_id           VARCHAR(36) NOT NULL,
    plan_id             VARCHAR(36) NOT NULL,
    incident_id         VARCHAR(36),
    decision            VARCHAR(30) NOT NULL,
    risk_score          INTEGER NOT NULL,
    confidence_score    FLOAT NOT NULL,
    validation_duration_ms FLOAT NOT NULL,
    environment         VARCHAR(50) NOT NULL,
    plan_type           VARCHAR(50) NOT NULL,
    rules_triggered     TEXT NOT NULL DEFAULT '[]',
    was_executed        BOOLEAN NOT NULL DEFAULT FALSE,
    execution_succeeded BOOLEAN,
    is_false_positive   BOOLEAN NOT NULL DEFAULT FALSE,
    is_false_negative   BOOLEAN NOT NULL DEFAULT FALSE,
    recorded_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvh_plan_id ON uaes_validation_history(plan_id);
CREATE INDEX idx_uvh_incident_id ON uaes_validation_history(incident_id);
CREATE INDEX idx_uvh_decision ON uaes_validation_history(decision);
CREATE INDEX idx_uvh_recorded_at ON uaes_validation_history(recorded_at);
CREATE INDEX idx_uvh_false_positive ON uaes_validation_history(is_false_positive);
CREATE INDEX idx_uvh_false_negative ON uaes_validation_history(is_false_negative);
```

#### uaes_policy_packs (NEW)

```sql
CREATE TABLE uaes_policy_packs (
    pack_id             VARCHAR(36) PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    description         TEXT NOT NULL,
    pack_type           VARCHAR(50) NOT NULL,
    enabled             BOOLEAN NOT NULL DEFAULT TRUE,
    policy_ids          TEXT NOT NULL DEFAULT '[]',
    priority            INTEGER NOT NULL DEFAULT 0,
    applicable_environments TEXT NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_upp_pack_type ON uaes_policy_packs(pack_type);
CREATE INDEX idx_upp_enabled ON uaes_policy_packs(enabled);
```

#### uaes_validator_plugins (NEW)

```sql
CREATE TABLE uaes_validator_plugins (
    plugin_id           VARCHAR(36) PRIMARY KEY,
    name                VARCHAR(100) NOT NULL,
    description         TEXT NOT NULL,
    version             VARCHAR(20) NOT NULL,
    plugin_type         VARCHAR(50) NOT NULL,
    enabled             BOOLEAN NOT NULL DEFAULT TRUE,
    provides_rules      TEXT NOT NULL DEFAULT '[]',
    provides_analyzers  TEXT NOT NULL DEFAULT '[]',
    dependencies        TEXT NOT NULL DEFAULT '[]',
    loaded_at           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvp_plugin_type ON uaes_validator_plugins(plugin_type);
CREATE INDEX idx_uvp_enabled ON uaes_validator_plugins(enabled);
```

#### uaes_validation_audit_log

```sql
CREATE TABLE uaes_validation_audit_log (
    log_id          VARCHAR(36) PRIMARY KEY,
    result_id       VARCHAR(36) REFERENCES uaes_validation_results(result_id),
    plan_id         VARCHAR(36),
    action          VARCHAR(50) NOT NULL,
    actor           VARCHAR(100) NOT NULL,
    details_json    TEXT NOT NULL DEFAULT '{}',
    ip_address      VARCHAR(45),
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uval_plan_id ON uaes_validation_audit_log(plan_id);
CREATE INDEX idx_uval_result_id ON uaes_validation_audit_log(result_id);
CREATE INDEX idx_uval_action ON uaes_validation_audit_log(action);
CREATE INDEX idx_uval_actor ON uaes_validation_audit_log(actor);
CREATE INDEX idx_uval_timestamp ON uaes_validation_audit_log(timestamp);
```

### 13.3 SQLAlchemy Models

SQLAlchemy models mirror the SQL schema above. All models use:
- `Mapped[str]` for string columns
- `Mapped[datetime]` for timestamp columns
- `relationship()` for foreign key relationships
- `Index()` for explicit indexes

---

## 14. REST API

### 14.1 Endpoint Overview

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/v1/validation/validate` | Submit plan for validation | developer+ |
| GET | `/api/v1/validation/results/{result_id}` | Get validation result | developer+ |
| GET | `/api/v1/validation/results/plan/{plan_id}` | Get result by plan ID | developer+ |
| GET | `/api/v1/validation/pending-approvals` | List pending approvals | maintainer+ |
| POST | `/api/v1/validation/approve/{request_id}` | Approve a plan | maintainer+ |
| POST | `/api/v1/validation/reject/{request_id}` | Reject a plan | maintainer+ |
| GET | `/api/v1/validation/permissions/{plan_id}` | Check execution permission | developer+ |
| DELETE | `/api/v1/validation/permissions/{plan_id}` | Revoke permission | admin+ |
| GET | `/api/v1/validation/rules` | List validation rules | developer+ |
| GET | `/api/v1/validation/policies` | List validation policies | developer+ |
| GET | `/api/v1/validation/history/{plan_id}` | Get validation history | developer+ |
| GET | `/api/v1/validation/statistics` | Get validation statistics | developer+ |
| GET | `/api/v1/validation/trends/{trend_type}` | Get validation trends | developer+ |
| GET | `/api/v1/validation/signatures/{plan_id}` | Get validation signature | developer+ |
| GET | `/api/v1/validation/explanation/{result_id}` | Get validation explanation | developer+ |

### 14.2 Request/Response Schemas

#### POST /api/v1/validation/validate

```python
class ValidatePlanRequest(BaseModel):
    plan_id: str
    incident_id: str | None = None
    plan_json: dict[str, Any]
    plan_type: str = "infrastructure_repair"
    environment: str = "production"
    priority: int = 0
    timeout_seconds: int = 300
    metadata: dict[str, Any] = {}

class ValidatePlanResponse(BaseModel):
    request_id: str
    status: str
    result: ValidationResultResponse | None = None
```

#### GET /api/v1/validation/results/{result_id}

```python
class ValidationResultResponse(BaseModel):
    result_id: str
    request_id: str
    plan_id: str
    decision: str
    decision_reason: str
    summary: str
    explanation: ValidationExplanationResponse | None = None
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    failures: list[ValidationFailureResponse]
    warnings: list[ValidationWarningResponse]
    approval_required: bool
    approval_level: str | None
    signature: ValidationSignatureResponse | None = None
    validated_at: str
    validation_duration_ms: float
```

#### POST /api/v1/validation/approve/{request_id}

```python
class ApprovePlanRequest(BaseModel):
    reason: str
    conditions: list[str] = []

class ApprovePlanResponse(BaseModel):
    decision_id: str
    decision: str
    decided_by: str
    expires_at: str
```

### 14.3 Authentication

All endpoints use `Depends(verify_token)` dependency injection.

```python
from fastapi import Depends, APIRouter
from app.core.security import verify_token

router = APIRouter(prefix="/api/v1/validation", tags=["validation"])


@router.post("/validate")
async def validate_plan(
    request: ValidatePlanRequest,
    token: dict = Depends(verify_token),
    validation_service: ValidationService = Depends(get_validation_service),
) -> ValidatePlanResponse:
    ...
```

---

## 15. Events

### 15.1 Event Overview

All events are published via `InProcessEventBus`.

| Event | Published When | Payload |
|-------|---------------|---------|
| ValidationRequested | Planner submits for validation | request_id, plan_id, environment |
| ValidationStarted | Engine begins validation | request_id, plan_id |
| ValidationCompleted | Engine finishes validation | request_id, result_id, decision |
| ValidationFailed | Engine encounters error | request_id, error, stack_trace |
| ValidationRuleTriggered | A specific rule fires | rule_code, result, failure/warning |
| ValidationBlockerDetected | Blocker found | failure_id, rule_code, reason |
| ValidationWarningGenerated | Warning generated | warning_id, rule_code, message |
| ValidationApprovalRequired | Needs human approval | request_id, approval_level, risk_score |
| ValidationApprovalGranted | Human approved | request_id, decided_by, conditions |
| ValidationApprovalRejected | Human rejected | request_id, decided_by, reason |
| ValidationApprovalEscalated | Escalated to higher authority | request_id, from_level, to_level |
| ValidationPermissionGranted | Execution permitted | plan_id, permission_id, expires_at |
| ValidationPermissionRevoked | Permission removed | plan_id, permission_id, reason |
| ValidationExpired | Validation window expired | request_id, plan_id |
| ValidationSignatureCreated | Digital signature created | plan_id, signature_id, signature_hash |
| ValidationSignatureVerified | Signature verified | plan_id, signature_id, valid |
| ValidationHistoryRecorded | History entry created | record_id, plan_id, decision |
| ValidationTrendComputed | Trend computed | trend_id, trend_type, period |
| ValidationCacheHit | Cache hit occurred | plan_id, cache_key |
| ValidationCacheMiss | Cache miss occurred | plan_id, cache_key |
| ValidationMetricsRecorded | Metrics emitted | request_id, duration_ms, decision |

### 15.2 Event Definitions

```python
class ValidationRequested(BaseModel):
    event_type: str = "validation.requested"
    request_id: str
    plan_id: str
    incident_id: str | None
    environment: str
    requested_by: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationCompleted(BaseModel):
    event_type: str = "validation.completed"
    request_id: str
    result_id: str
    plan_id: str
    decision: str
    validation_duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationBlockerDetected(BaseModel):
    event_type: str = "validation.blocker_detected"
    request_id: str
    result_id: str
    failure_id: str
    rule_code: str
    rule_name: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationApprovalRequired(BaseModel):
    event_type: str = "validation.approval_required"
    request_id: str
    plan_id: str
    approval_level: str
    risk_score: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationPermissionGranted(BaseModel):
    event_type: str = "validation.permission_granted"
    plan_id: str
    permission_id: str
    result_id: str
    granted_by: str
    expires_at: datetime
    conditions: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationSignatureCreated(BaseModel):
    event_type: str = "validation.signature_created"
    plan_id: str
    signature_id: str
    signature_hash: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationHistoryRecorded(BaseModel):
    event_type: str = "validation.history_recorded"
    record_id: str
    plan_id: str
    decision: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationCacheHit(BaseModel):
    event_type: str = "validation.cache_hit"
    plan_id: str
    cache_key: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 15.3 Event Flow

```
                    ┌──────────────────────┐
                    │   Validation Engine  │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
   │  Validation     │ │  Monitoring   │ │  Execution     │
   │  History        │ │  Engine       │ │  Engine        │
   └────────────────┘ └───────────────┘ └────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
   HistoryRecorded      Metrics Recorded    Permission Checked
   TrendComputed        Health Updated      Signature Verified
   FalsePositiveTracked                     Execution Starts
```

---

## 16. Integration

### 16.1 Planner Integration

The Validation Engine subscribes to the `PlanGenerated` event from the Planner.

```
Planner                          Validation Engine
   │                                   │
   │  PlanGenerated(event)             │
   │──────────────────────────────────▶│
   │                                   │
   │                                   │ Create ValidationRequest
   │                                   │ Run pipeline
   │                                   │
   │  ValidationCompleted(event)       │
   │◀──────────────────────────────────│
```

### 16.2 Execution Engine Integration

The Execution Engine checks for an active `ExecutionPermission` and valid `ValidationSignature` before executing.

```
Execution Engine                   Validation Engine
      │                                   │
      │  CheckPermission(plan_id)         │
      │──────────────────────────────────▶│
      │                                   │
      │  PermissionGranted / Denied       │
      │◀──────────────────────────────────│
      │                                   │
      │  VerifySignature(plan_id)         │
      │──────────────────────────────────▶│
      │                                   │
      │  SignatureValid / Invalid         │
      │◀──────────────────────────────────│
      │                                   │
      │  (if both valid) Execute plan     │
```

### 16.3 Monitoring Integration

The Validation Engine reads health metrics and resource utilization from the Monitoring Engine.

```
Monitoring Engine                  Validation Engine
      │                                   │
      │  GetResourceMetrics()             │
      │◀──────────────────────────────────│
      │                                   │
      │  ResourceMetrics                  │
      │──────────────────────────────────▶│
      │                                   │
      │                                   │ Feed into ResourceAssessment
```

### 16.4 Incidents Integration

The Validation Engine reads incident severity and root cause category.

```
Incident System                    Validation Engine
      │                                   │
      │  GetIncidentDetails(incident_id)  │
      │◀──────────────────────────────────│
      │                                   │
      │  IncidentDetails                  │
      │──────────────────────────────────▶│
      │                                   │
      │                                   │ Feed into SafetyAssessment
```

### 16.5 Event Bus Integration

```python
# Event bus wiring
event_bus.subscribe("plan_generated", validation_service.handle_plan_generated)
event_bus.subscribe("validation_completed", execution_engine.handle_validation_completed)
event_bus.subscribe("validation_blocker_detected", notification_service.handle_blocker)
event_bus.subscribe("validation_approval_required", approval_service.handle_approval_required)
event_bus.subscribe("validation_signature_created", signature_service.handle_signature_created)
```

### 16.6 Learning Engine Integration (Future)

The Learning Engine (Sprint 7) will consume validation history and trends:

```
Validation Engine                  Learning Engine
      │                                   │
      │  ValidationHistoryRecorded        │
      │──────────────────────────────────▶│
      │                                   │
      │  ValidationTrendComputed          │
      │──────────────────────────────────▶│
      │                                   │
      │                                   │ Learn patterns
      │                                   │ Update rules
      │                                   │ Improve predictions
      │                                   │
      │  RulesUpdated                     │
      │◀──────────────────────────────────│
```

### 16.7 Knowledge Graph Integration (Future)

The Knowledge Graph will store validation patterns:

```
Validation Engine                  Knowledge Graph
      │                                   │
      │  QueryValidationPatterns()        │
      │◀──────────────────────────────────│
      │                                   │
      │  ValidationPatterns               │
      │──────────────────────────────────▶│
      │                                   │
      │  StoreValidationOutcome()         │
      │──────────────────────────────────▶│
```

### 16.8 Memory System Integration (Future)

The Memory System will store validation context:

```
Validation Engine                  Memory System
      │                                   │
      │  StoreValidationContext()         │
      │──────────────────────────────────▶│
      │                                   │
      │  RecallSimilarValidations()       │
      │◀──────────────────────────────────│
```

---

## 17. Learning Integration

### 17.1 Purpose

The Learning Engine continuously improves the entire UAES by learning from execution outcomes. It receives information from every stage and feeds improvements back.

### 17.2 Information Sources

| Source | Information Provided |
|--------|---------------------|
| Monitoring | Health metrics, repair effectiveness, system state changes |
| Incident Detection | Incident patterns, root cause categories, severity distributions |
| Root Cause Analysis | Causal relationships, pattern matches, diagnostic accuracy |
| Planner | Strategy success rates, plan quality metrics, confidence calibration |
| Validation | Rule accuracy, false positive/negative rates, approval patterns |
| Execution | Execution success/failure rates, rollback effectiveness, duration accuracy |

### 17.3 Feedback Loops

```
                    ┌─────────────────────────────────────────────┐
                    │              LEARNING ENGINE                │
                    └──────────────────┬──────────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
  ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
  │   MONITORING  │          │   PLANNER     │          │   VALIDATION  │
  │               │          │               │          │               │
  │ • Thresholds  │          │ • Strategies  │          │ • Rules       │
  │ • Metrics     │          │ • Weights     │          │ • Policies    │
  │ • Alerts      │          │ • Confidence  │          │ • Thresholds  │
  └───────────────┘          └───────────────┘          └───────────────┘

Feedback Examples:
- Execution success → Validation history → Rule weight increase
- Execution failure → Planner penalties → Strategy adjustment
- Monitoring verification → Repair effectiveness → Threshold update
- False positive → Validation rules → Rule refinement
- False negative → Validation rules → New rule creation
```

### 17.4 Continuous Improvements

| Area | What Learning Improves |
|------|----------------------|
| Risk Estimation | Adjusts risk scores based on actual outcomes |
| Confidence Estimation | Calibrates confidence predictions |
| Repair Ranking | Improves strategy selection weights |
| Approval Prediction | Optimizes approval level determination |
| Rollback Recommendation | Improves rollback feasibility predictions |
| Simulation Prediction | Improves simulation accuracy |
| Future Plan Generation | Enhances planner strategy selection |
| Validation Policies | Optimizes policy pack configurations |

### 17.5 Data Flow

```
Execution Completed
       │
       ▼
┌──────────────┐
│   Learning   │
│   Engine     │
└──────┬───────┘
       │
       ├──▶ Update Validation History
       │    (record success/failure)
       │
       ├──▶ Update Rule Weights
       │    (increase weight of accurate rules)
       │
       ├──▶ Update Planner Strategies
       │    (prefer strategies with high success)
       │
       ├──▶ Update Risk Models
       │    (recalibrate risk scoring)
       │
       └──▶ Update Confidence Models
            (recalibrate confidence scoring)
```

---

## 18. Architecture Constraints

### 18.1 System Constraints

| Constraint | Description |
|-----------|-------------|
| Monitoring never calls Planner directly | Monitoring observes and reports. It does not trigger repairs. |
| Planner never executes repairs | Planner produces plans. Execution Engine executes. |
| Execution never bypasses Validation | No plan executes without passing validation. |
| Validation never modifies plans | Validation verifies plans. It does not change them. |
| Learning never modifies historical records | Learning adds new knowledge. It does not alter history. |
| Only services may orchestrate contexts | Contexts are built by services, not analyzers. |
| All analyzers remain stateless | Analyzers have no internal state between calls. |
| ValidationContext is immutable | Once built, context cannot be modified. |
| Bounded contexts remain isolated | Each context depends on nothing outside its boundary. |

### 18.2 Data Flow Constraints

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW RULES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Monitoring ──▶ Incident Detection ──▶ Root Cause Analysis  │
│       │                                        │            │
│       │ (read-only)                           │ (read-only) │
│       ▼                                        ▼            │
│  Validation ◄─────────────────────────────── Planner        │
│       │                                        ▲            │
│       │ (read-only)                           │ (read-only) │
│       ▼                                        │            │
│  Execution ──────────────────────────────▶ Learning         │
│                                                             │
│  Rules:                                                     │
│  • Arrows show data flow direction                          │
│  • (read-only) means the source cannot modify the target   │
│  • Learning feeds back to all stages (not shown for clarity)│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 18.3 Immutability Constraints

| Object | Immutable? | Mutated By |
|--------|-----------|------------|
| ValidationContext | YES | Nobody (built once) |
| ValidationRequest | YES | Nobody (created once) |
| ValidationDecision | YES | DecisionEngine (created once) |
| ValidationRule | YES | RuleRepository (update via replacement) |
| ValidationPolicy | YES | PolicyRepository (update via replacement) |
| AuditLogEntry | YES | Nobody (append-only) |
| ValidationSignature | YES | Nobody (created once) |

### 18.4 Bounded Context Isolation

Each bounded context:
- Has its own domain, application, infrastructure, and API layers
- Depends on nothing outside its boundary except shared kernel types
- Communicates with other contexts only via events or explicit APIs
- Cannot directly access another context's database or internal state

### 18.5 Service Orchestration Rules

| Rule | Description |
|------|-------------|
| Services orchestrate | Only services may coordinate multiple analyzers |
| Analyzers analyze | Analyzers only read context and return assessments |
| Repositories persist | Repositories only store and retrieve data |
| Events communicate | Contexts communicate via domain events |
| APIs expose | APIs expose functionality to external consumers |

---

## 19. Failure Modes

### 19.1 Failure Mode Matrix

| Failure Mode | Detection | Response | Recovery |
|-------------|-----------|----------|----------|
| Validation crashes | Process restart | Revalidate on retry | Idempotent via request_id |
| Rules unavailable | Repository query fails | Default to most restrictive | Block all until rules restored |
| Database unavailable | Connection pool exhaustion | In-memory validation | Degrade persistence |
| Simulation unavailable | Timeout / connection error | Treat as "not simulated" | Warning, not blocker |
| Approval unavailable | Timeout / queue full | Queue for later | Timeout escalation |
| External dependency unavailable | Connection error | Log, skip non-critical | Retry with backoff |
| Cache unavailable | Connection error | Skip cache, run pipeline | Retry with backoff |
| Plugin unavailable | Load failure | Disable plugin, continue | Retry plugin load |

### 19.2 Graceful Degradation

**Validation crashes**: The pipeline is idempotent via `request_id`. No partial state is persisted.

**Rules unavailable**: Default to **most restrictive** mode: all plans are rejected.

**Database unavailable**: In-memory validation. Results not persisted but decision returned.

**Simulation unavailable**: Marked as "not_performed". Warning unless high risk.

**Approval unavailable**: Stored with `PENDING_APPROVAL` status. Timeout escalation applies.

**Cache unavailable**: Skip cache, run full pipeline. Results not cached.

**Plugin unavailable**: Disable plugin, continue with built-in rules.

### 19.3 Idempotency

Every validation request carries a unique `request_id`. The pipeline is idempotent:

- If a request with the same `request_id` is submitted twice, the second returns the existing result
- Rule evaluations are deterministic given the same input
- Approval decisions are idempotent

---

## 20. Security

### 20.1 Authentication

All API endpoints use JWT-based authentication via `Depends(verify_token)`.

### 20.2 Authorization

Role-based access control (RBAC) with 5 roles:

| Role | Permissions |
|------|------------|
| `developer` | Submit validation, view results, view rules/policies |
| `maintainer` | + Approve/reject plans, view pending approvals |
| `operations` | + Manage rules/policies, emergency override |
| `administrator` | + Revoke permissions, manage audit logs |
| `emergency` | + Emergency override with full audit |

### 20.3 Audit Logging

Every decision is logged with actor, timestamp, IP, details, and action.

### 20.4 Tamper Protection

The audit log is append-only with planned hash-chain integrity.

### 20.5 Approval Recording

The full approval chain is recorded with who, when, conditions, and level.

### 20.6 Signature Verification

Digital signatures are verified before execution:

1. Execution Engine receives plan
2. Queries `ValidationSignature` by `plan_id`
3. Recomputes hash of `(plan_json + decision + timestamp)`
4. Compares with stored `signature_hash`
5. If match, execution proceeds
6. If mismatch, execution blocked

---

## 21. Performance

### 21.1 Latency Targets

| Scenario | Target Latency |
|----------|---------------|
| Auto-approved (dev/staging) | < 500ms |
| Approval-required | < 2s |
| Complex validation (>20 rules) | < 5s |
| Cache hit | < 50ms |
| Database round-trip | < 50ms |

### 21.2 Caching Strategy

**Validation results** are cached with:
- **Key**: SHA-256 of `(plan_json, environment, rules_version, policies_version)`
- **TTL**: 5 minutes default
- **Max entries**: 10,000
- **Eviction**: LRU

**Rules and policies** are cached in-memory with 5-minute TTL.

### 21.3 Scalability

- **Horizontal scaling**: Stateless engine, multiple instances behind load balancer
- **Validation workers**: Separate workers for pipeline stages
- **Database**: Connection pooling, read replicas

### 21.4 Concurrency

All service methods are `async`. Independent analyzers run concurrently via `asyncio.gather`.

### 21.5 Throughput

- **Target**: 100 validations/second sustained
- **Burst**: 500 validations/second for 10 seconds
- **Cache hit throughput**: 1000 validations/second

---

## 22. Testing Strategy

### 22.1 Unit Tests

- **100% rule coverage**: Every validation rule (40+) has at least one test
- **All domain models**: Every model tested for construction, validation, serialization
- **All value objects**: Range validation, property methods, edge cases
- **All enums**: Verify string values, membership, serialization
- **Service unit tests**: Mocked repositories, verify logic in isolation

### 22.2 Integration Tests

- **Full pipeline**: End-to-end validation with real repositories
- **Repository round-trips**: Save and retrieve each model type
- **Event dispatch**: Verify events are published on correct triggers
- **API endpoint tests**: Full HTTP request/response cycle
- **Database migrations**: Verify migration up/down works correctly

### 22.3 Stress Tests

- **Concurrent validations**: 100 simultaneous validation requests
- **Timeout handling**: Validation timeout triggers correctly
- **Connection pool exhaustion**: Graceful degradation under DB pressure
- **Memory pressure**: Large number of cached rules/policies

### 22.4 Chaos Tests

- **Database failure**: In-memory validation works correctly
- **Rule engine failure**: Default to restrictive mode
- **Approval timeout**: Escalation triggers correctly
- **Partial validation**: Pipeline halts on blocker, produces correct partial result

### 22.5 Failure Simulation

- **Rule engine crash recovery**: Pipeline recovers and produces valid result
- **Partial validation**: Some analyzers succeed, others fail — decision still made
- **Approval system down**: Queued for later, timeout escalation still works

### 22.6 Test File Map

```
tests/unit/
├── test_validation_request.py
├── test_validation_result.py
├── test_validation_decision.py
├── test_validation_rule.py
├── test_validation_policy.py
├── test_validation_evidence.py
├── test_validation_failure.py
├── test_validation_warning.py
├── test_approval_decision.py
├── test_execution_permission.py
├── test_execution_blocker.py
├── test_safety_assessment.py
├── test_compatibility_assessment.py
├── test_rollback_assessment.py
├── test_simulation_assessment.py
├── test_dependency_assessment.py
├── test_resource_assessment.py
├── test_security_assessment.py
├── test_cost_assessment.py
├── test_validation_explanation.py
├── test_validation_signature.py
├── test_validation_history.py
├── test_validation_statistics.py
├── test_validation_trend.py
├── test_validation_cache_entry.py
├── test_policy_pack.py
├── test_validator_plugin.py
├── test_confidence_score.py
├── test_risk_score.py
├── test_time_range.py
├── test_threshold_range.py
├── test_component_descriptor.py
├── test_environment_descriptor.py
├── test_version_constraint.py
├── test_resource_quota.py
├── test_maintenance_window.py
├── test_rule_engine.py
├── test_policy_engine.py
├── test_approval_engine.py
├── test_decision_engine.py
├── test_summary_generator.py
├── test_explainability_service.py
├── test_history_service.py
├── test_trend_service.py
├── test_cache_service.py
└── test_plugin_manager.py

tests/integration/
├── test_validation_pipeline.py
├── test_validation_repository.py
├── test_rule_repository.py
├── test_policy_repository.py
├── test_evidence_repository.py
├── test_audit_repository.py
├── test_signature_repository.py
├── test_history_repository.py
├── test_event_dispatch.py
└── test_full_validation_flow.py

tests/stress/
├── test_concurrent_validations.py
└── test_timeout_handling.py

tests/chaos/
├── test_database_failure.py
├── test_rule_engine_failure.py
├── test_approval_timeout.py
└── test_partial_validation.py
```

---

## 23. Definition of Done

### 23.1 Domain Layer

- [ ] All 26+ domain models implemented with `frozen=True` and `use_enum_values=True`
- [ ] All 9 value objects implemented with validation
- [ ] All 16 enums implemented as `StrEnum`
- [ ] Domain events defined and typed
- [ ] Domain layer has zero external dependencies

### 23.2 Application Layer

- [ ] All 20+ services implemented
- [ ] All repository port interfaces defined as `Protocol`
- [ ] Event publisher port interface defined
- [ ] Validation pipeline complete (13 stages)
- [ ] Pipeline is idempotent via `request_id`
- [ ] ExplainabilityService generates detailed explanations
- [ ] ValidationHistoryService stores and queries history
- [ ] TrendAnalysisService computes trends
- [ ] ValidationCacheService caches results
- [ ] PluginManager discovers and loads plugins
- [ ] PolicyPackLoader selects appropriate packs

### 23.3 Infrastructure Layer

- [ ] All 11 database tables with SQLAlchemy ORM models
- [ ] Alembic migration created and tested (up/down)
- [ ] All 9 repository implementations with async SQLAlchemy
- [ ] In-process event publisher implemented
- [ ] Validation cache with LRU eviction
- [ ] Rule/policy cache with 5-minute TTL

### 23.4 API Layer

- [ ] All 15 REST endpoints implemented
- [ ] Request/response schemas defined
- [ ] `Depends(verify_token)` auth on all endpoints
- [ ] OpenAPI docs auto-generated

### 23.5 Rules & Policies

- [ ] All 35+ rules implemented (8 Safety, 5 Dependency, 5 Compatibility, 5 Resource, 8 Policy, 4 Security, 4 Rollback)
- [ ] Policy pack system working
- [ ] Plugin-provided rules supported

### 23.6 Approval System

- [ ] 6-level hierarchy (AUTO → DEVELOPER → MAINTAINER → OPERATIONS → ADMINISTRATOR → EMERGENCY)
- [ ] Escalation matrix working
- [ ] Timeout rules working
- [ ] Delegation rules working
- [ ] Conditional approval working
- [ ] State transitions working

### 23.7 Digital Signature

- [ ] ValidationSignature created on approved plans
- [ ] Signature hash computation working
- [ ] Signature verification working
- [ ] Signature expiry working

### 23.8 Events

- [ ] All 21 typed domain events
- [ ] Published on correct triggers
- [ ] Consumed by downstream

### 23.9 Testing

- [ ] 692+ existing tests pass
- [ ] 200+ new validation tests
- [ ] 100% rule/model coverage
- [ ] Integration/stress/chaos tests

### 23.10 Code Quality

- [ ] `ruff check` clean
- [ ] `ruff format` clean
- [ ] No circular dependencies
- [ ] No domain leaks
- [ ] Architecture doc frozen

---

## 24. Validation History Intelligence

### 24.1 Purpose

The Validation History Intelligence system stores every validation result, tracks outcomes, and provides historical context for future validations. This enables the Learning Engine (Sprint 7) to improve validation accuracy over time.

### 24.2 Responsibilities

| Responsibility | Description |
|---------------|-------------|
| Store validation results | Every request and result stored permanently |
| Track approval/rejection history | Who approved/rejected what, when |
| Track validation duration | Average, p95, p99 latency |
| Track false positives | Plan approved but execution failed |
| Track false negatives | Plan rejected but would have succeeded |
| Store recurring failures | Rules that fail repeatedly |
| Maintain statistics | Success rate, approval rate, average duration |
| Predict outcomes | Predict validation outcome based on history |

### 24.3 False Positive/Negative Tracking

```
False Positive Flow:
1. Plan approved by Validation Engine
2. Plan executed by Execution Engine
3. Execution fails
4. Learning Engine records false positive
5. ValidationHistoryService updates record
6. TrendAnalysisService updates failure trend
7. Future similar plans receive warnings

False Negative Flow:
1. Plan rejected by Validation Engine
2. User manually executes plan
3. Execution succeeds
4. Learning Engine records false negative
5. ValidationHistoryService updates record
6. TrendAnalysisService updates confidence trend
7. Future similar plans receive higher confidence
```

### 24.4 Learning Engine Integration

```python
# Learning Engine consumes validation history
class LearningEngine:
    async def learn_from_history(
        self,
        history: list[ValidationHistoryRecord],
    ) -> LearningResult:
        """Learn patterns from validation history."""
        # Analyze false positives
        # Analyze false negatives
        # Identify recurring failures
        # Update rule weights
        # Improve confidence predictions
        ...
```

### 24.5 Recurring Failure Detection

```python
# Detect rules that fail repeatedly
async def get_recurring_failures(
    self,
    *,
    rule_code: str | None = None,
    min_occurrences: int = 5,
    time_window_days: int = 30,
) -> list[RecurringFailure]:
    """Get rules that fail repeatedly."""
    ...
```

---

## 25. Explainable Validation

### 25.1 Purpose

Every validation result must include detailed explanations. This ensures transparency, auditability, and enables humans to understand why a decision was made.

### 25.2 Explanation Components

| Component | Description |
|-----------|-------------|
| Detailed reasons | Why the decision was made |
| Failed rules | Which rules failed and why |
| Warning rules | Which rules warned and why |
| Confidence explanation | Why confidence is at this level |
| Suggested fixes | How to fix the issues |
| Strategy recommendation | Recommended planner strategy |
| Dependency explanation | Dependency impact explanation |
| Rollback explanation | Rollback feasibility explanation |
| Evidence summary | Summary of evidence collected |

### 25.3 Explanation Generation

The `ExplainabilityService` generates explanations by:

1. Collecting all assessment results
2. Analyzing failed rules and their reasons
3. Analyzing warnings and their implications
4. Computing confidence explanation from confidence score
5. Generating dependency explanation from dependency assessment
6. Generating rollback explanation from rollback assessment
7. Synthesizing suggested fixes from all failures
8. Generating overall summary

### 25.4 Example Explanation

```json
{
  "summary": "Plan rejected due to safety concerns. Database restart detected during active migration.",
  "detailed_reasons": [
    "SAFETY_001: Database restart blocked during active migration",
    "ROLLBACK_001: Rollback not available for database operations"
  ],
  "failed_rules_explanation": "The plan triggers SAFETY_001 because an active migration was detected on the target database. This rule prevents data corruption during schema changes.",
  "warning_rules_explanation": "ROLLBACK_003 warns that rollback success rate is 75%, below the 80% threshold.",
  "confidence_explanation": "Confidence is 0.4 (low) due to the presence of an active migration and limited rollback options.",
  "dependency_explanation": "The plan affects 3 direct dependencies and 12 reverse dependencies. Cascade risk is MEDIUM.",
  "rollback_explanation": "Rollback is available but not automatic. Estimated rollback time is 300 seconds. Rollback has not been tested for this specific operation.",
  "suggested_fixes": [
    "Wait for migration to complete before restarting database",
    "Test rollback procedure in staging environment",
    "Increase confidence score by adding simulation results"
  ],
  "strategy_recommendation": "Consider using a rolling restart strategy instead of a full restart to maintain availability during migration.",
  "evidence_summary": "Evidence collected from: EnvironmentAnalyzer (migration status), DependencyAnalyzer (service graph), RollbackAnalyzer (rollback history)"
}
```

---

## 26. AI Validator Extension Point

### 26.1 Purpose

The AI Validator is an optional extension point that allows AI-assisted validation. This is **NOT implemented now** — only the architecture is defined.

### 26.2 Pipeline Position

```
Stage 10: Rule Engine
    │
    ▼
Stage 11: Policy Engine
    │
    ▼
Stage 12: AI Validator (Optional)  ← NEW
    │
    ▼
Stage 13: Decision Engine
```

### 26.3 Interface Definition

```python
class AIValidatorProtocol(Protocol):
    """Protocol for AI-assisted validation."""

    async def analyze(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
        rule_results: tuple[list[ValidationFailure], list[ValidationWarning]],
    ) -> AIValidationResult:
        """Analyze the plan using AI models."""
        ...

    def get_confidence(self) -> ConfidenceScore:
        """Get confidence in the AI analysis."""
        ...

    def get_recommendation(self) -> str:
        """Get human-readable recommendation."""
        ...


class AIValidationResult(BaseModel):
    """Result from AI validation."""
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    recommendation: str                          # "approve", "reject", "conditional"
    confidence: ConfidenceScore
    reasoning: str                               # Why the AI recommends this
    risk_factors: list[str] = []                 # Identified risk factors
    suggested_modifications: list[str] = []      # Suggested plan modifications
    similar_historical_cases: list[str] = []     # Similar past validations
```

### 26.4 Future Implementation

When implemented, the AI Validator could use:
- Machine learning models trained on validation history
- Natural language processing for plan analysis
- Pattern matching against known failure modes
- Predictive analytics for risk assessment

---

## 27. Validation Cache

### 24.1 Purpose

The Validation Cache stores validation results for identical plans to avoid redundant computation.

### 27.2 Cache Key Computation

```python
def compute_cache_key(
    plan_json: dict[str, Any],
    environment: str,
    rules_version: str,
    policies_version: str,
) -> str:
    """Compute SHA-256 cache key."""
    key_data = f"{json.dumps(plan_json, sort_keys=True)}:{environment}:{rules_version}:{policies_version}"
    return hashlib.sha256(key_data.encode()).hexdigest()
```

### 27.3 Cache Invalidation

| Trigger | Action |
|---------|--------|
| Rule update | Invalidate entries affected by changed rules |
| Policy update | Invalidate entries affected by changed policies |
| TTL expiry | Auto-invalidate after 5 minutes |
| Manual invalidation | API endpoint to clear cache |

### 27.4 Cache Storage

```python
class ValidationCacheBackend(Protocol):
    async def get(self, cache_key: str) -> ValidationCacheEntry | None: ...
    async def put(self, entry: ValidationCacheEntry) -> None: ...
    async def invalidate(self, cache_key: str) -> bool: ...
    async def clear(self) -> int: ...
    async def size(self) -> int: ...
```

### 27.5 Cache Configuration

```python
class CacheConfig(BaseModel):
    ttl_seconds: int = 300                        # 5 minutes
    max_entries: int = 10000                      # LRU eviction
    enabled: bool = True
    warm_on_startup: bool = False                 # Pre-populate cache
```

---

## 28. Digital Signature

### 28.1 Purpose

Digital signatures ensure that approved plans cannot be tampered with before execution. The Execution Engine verifies signatures before executing.

### 28.2 Signature Creation

```python
def create_signature(
    plan_json: dict[str, Any],
    decision: str,
    timestamp: datetime,
    approved_by: str,
) -> ValidationSignature:
    """Create a digital signature for an approved plan."""
    # Compute hash
    data = f"{json.dumps(plan_json, sort_keys=True)}:{decision}:{timestamp.isoformat()}"
    signature_hash = hashlib.sha256(data.encode()).hexdigest()

    return ValidationSignature(
        signature_id=str(uuid.uuid4()),
        result_id=result_id,
        plan_id=plan_id,
        signature_hash=signature_hash,
        signed_at=timestamp,
        signed_by=approved_by,
        approval_metadata={"decision": decision},
        verification_method="sha256",
    )
```

### 28.3 Signature Verification

```python
def verify_signature(
    signature: ValidationSignature,
    plan_json: dict[str, Any],
    decision: str,
    timestamp: datetime,
) -> bool:
    """Verify a digital signature."""
    # Recompute hash
    data = f"{json.dumps(plan_json, sort_keys=True)}:{decision}:{timestamp.isoformat()}"
    expected_hash = hashlib.sha256(data.encode()).hexdigest()

    # Compare
    return signature.signature_hash == expected_hash
```

### 28.4 Future Cryptographic Implementation

Future enhancement: RSA or ECDSA signatures for stronger security.

---

## 29. Validation Trend Analysis

### 29.1 Purpose

Historical trend tracking enables the system to understand how validation metrics change over time.

### 29.2 Trend Types

| Trend Type | Description | Time Windows |
|------------|-------------|--------------|
| Risk trend | 7-day rolling average of risk scores | 7d, 30d, 90d |
| Confidence trend | 7-day rolling average of confidence scores | 7d, 30d, 90d |
| Failure trend | Failures per day | 7d, 30d, 90d |
| Approval trend | Approvals vs rejections per day | 7d, 30d, 90d |
| Latency trend | p50, p95, p99 validation duration | 7d, 30d, 90d |

### 29.3 Trend Direction

```python
def compute_trend_direction(data_points: list[float]) -> str:
    """Compute trend direction from data points."""
    if len(data_points) < 2:
        return "stable"

    # Simple linear regression
    x = list(range(len(data_points)))
    y = data_points
    slope = (len(x) * sum(x_i * y_i for x_i, y_i in zip(x, y)) - sum(x) * sum(y)) / \
            (len(x) * sum(x_i ** 2 for x_i in x) - sum(x) ** 2)

    if slope > 0.01:
        return "improving"
    elif slope < -0.01:
        return "degrading"
    else:
        return "stable"
```

### 29.4 Consumer Integration

| Consumer | Usage |
|----------|-------|
| Monitoring Engine | Display trend dashboards |
| Learning Engine | Identify patterns, update rules |
| Operations Team | Manual review of degrading trends |
| Alerting System | Trigger alerts on degrading trends |

---

## 30. Generic Validation Framework

### 30.1 Purpose

The Validation Engine is designed to validate multiple types of plans, not just infrastructure repairs.

### 30.2 Supported Plan Types

| Plan Type | Description | Example |
|-----------|-------------|---------|
| `infrastructure_repair` | Infrastructure remediation | Restart service, scale deployment |
| `deployment` | Application deployment | Deploy new version, rollback |
| `automation` | Automated tasks | Scheduled maintenance, cleanup |
| `financial` | Financial strategies | Portfolio rebalancing, trading |
| `ai_workflow` | AI/ML workflows | Model training, inference |
| `stock_trading` | Stock trading strategies | Buy/sell orders, hedging |
| `custom` | Custom plan types | User-defined validation |

### 30.3 Generic Terminology

| Infrastructure Term | Generic Term |
|--------------------|--------------|
| Service | Component |
| Restart | Execute |
| Repair | Plan |
| Incident | Event |
| Deployment | Action |

### 30.4 Plan-Type-Specific Rules

Rules can be scoped to specific plan types:

```python
class ValidationRule(BaseModel):
    plan_types: list[str] = []                   # Empty = all plan types
    # If plan_types = ["infrastructure_repair"], rule only applies to infrastructure repairs
```

---

## 31. Policy Packs

### 31.1 Purpose

Policy Packs group related policies for different contexts. Different environments use different packs.

### 31.2 Pack Types

| Pack Type | Description | Example Policies |
|-----------|-------------|------------------|
| `production` | Production environment | Maintenance window, approval requirements |
| `development` | Development environment | Relaxed approval, auto-deploy |
| `testing` | Testing environment | Test-only restrictions |
| `infrastructure` | Infrastructure changes | Database, Redis, network policies |
| `financial` | Financial operations | Budget limits, trading restrictions |
| `personal_assistant` | Personal assistant | Calendar, email, task policies |
| `experimental` | Experimental features | New feature validation |
| `custom` | Custom packs | User-defined policies |

### 31.3 Pack Selection

```python
def select_pack(
    request: ValidationRequest,
    available_packs: list[PolicyPack],
) -> PolicyPack:
    """Select the appropriate policy pack."""
    # 1. Check for plan-type-specific pack
    for pack in available_packs:
        if pack.pack_type == request.plan_type:
            return pack

    # 2. Check for environment-specific pack
    for pack in available_packs:
        if request.environment in pack.applicable_environments:
            return pack

    # 3. Default to production pack
    return next(p for p in available_packs if p.pack_type == "production")
```

### 31.4 Pack Loading

```python
class PolicyPackLoader:
    async def load_pack(
        self,
        pack_id: str,
    ) -> PolicyPack:
        """Load a policy pack and its policies."""
        pack = await self._repository.get_pack_by_id(pack_id)
        policies = await self._load_policies(pack.policy_ids)
        return pack, policies
```

---

## 32. Validator Plugin System

### 32.1 Purpose

The Plugin System enables extensible validation with custom validators for different technologies and domains.

### 32.2 Plugin Types

| Plugin Type | Examples |
|-------------|----------|
| `infrastructure` | Docker, Linux, Windows |
| `cloud` | AWS, Azure, Google Cloud |
| `database` | PostgreSQL, MySQL, MongoDB |
| `financial` | Stock Market, Trading APIs |
| `calendar` | Google Calendar, Outlook |
| `communication` | Email, Slack, Teams |
| `custom` | Enterprise-specific validators |

### 32.3 Plugin Interface

```python
class ValidatorPluginProtocol(Protocol):
    """Protocol for validator plugins."""

    plugin_id: str
    name: str
    version: str

    async def initialize(self) -> None:
        """Initialize the plugin."""
        ...

    async def get_rules(self) -> list[ValidationRule]:
        """Get rules provided by this plugin."""
        ...

    async def get_analyzers(self) -> dict[str, Any]:
        """Get analyzers provided by this plugin."""
        ...

    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        ...
```

### 32.4 Plugin Discovery

Plugins are discovered from:
1. Database registry (`uaes_validator_plugins` table)
2. Plugin directory scanning
3. Configuration file

### 32.5 Plugin Registration

```python
class PluginManager:
    async def register_plugin(
        self,
        plugin: ValidatorPlugin,
    ) -> None:
        """Register a new plugin."""
        await self._repository.save_plugin(plugin)
        await self._load_plugin(plugin.plugin_id)
```

### 32.6 Plugin Lifecycle

```
Discovery → Registration → Loading → Initialization → Ready → Cleanup
```

### 32.7 Plugin Dependency Injection

Plugins receive dependencies via constructor injection:

```python
class MyPlugin:
    def __init__(
        self,
        *,
        rule_repository: RuleRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._rule_repository = rule_repository
        self._event_publisher = event_publisher
```

---

## 33. Future Integration

### 33.1 Sprint 6: Execution Engine

The Execution Engine will:
- Query `CheckPermission(plan_id)` before executing
- Verify `ValidationSignature` before executing
- Report execution outcomes back to ValidationHistoryService

### 33.2 Sprint 7: Learning Engine

The Learning Engine will:
- Consume validation history and trends
- Identify patterns in false positives/negatives
- Update rule weights based on historical accuracy
- Improve confidence predictions
- Suggest new rules based on failure patterns

### 33.3 Sprint 8: Autonomous Orchestrator

The Autonomous Orchestrator will:
- Use validation results to make autonomous decisions
- Coordinate multiple validation pipelines
- Manage validation priorities dynamically

### 33.4 Knowledge Graph

The Knowledge Graph will:
- Store validation patterns and outcomes
- Enable pattern-based validation
- Support semantic search of validation history

### 33.5 Memory System

The Memory System will:
- Store validation context for each plan
- Recall similar validations for comparison
- Provide contextual recommendations

### 33.6 Stock Market Intelligence

Future integration with stock market data for financial validation.

### 33.7 Financial Intelligence

Future integration with financial data for portfolio validation.

### 33.8 AI Decision Engine

Future integration with AI models for autonomous validation decisions.

### 33.9 Self-Healing Infrastructure

Future integration with self-healing systems for automatic remediation validation.

---

## Appendix A: UAES System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ULTRON AUTONOMOUS EXECUTION SYSTEM                       │
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │              │     │              │     │              │                │
│  │  MONITORING  │────▶│  INCIDENT    │────▶│  ROOT CAUSE  │                │
│  │              │     │  DETECTION   │     │  ANALYSIS    │                │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                │
│         │                                          │                        │
│         │ (health metrics)                         │ (root cause)           │
│         │                                          ▼                        │
│         │                                   ┌──────────────┐                │
│         │                                   │              │                │
│         │                                   │   PLANNER    │                │
│         │                                   │              │                │
│         │                                   └──────┬───────┘                │
│         │                                          │                        │
│         │                                          │ (repair plan)          │
│         │                                          ▼                        │
│         │                                   ┌──────────────┐                │
│         │                                   │              │                │
│         │◀──────────────────────────────────│  VALIDATION  │                │
│         │ (health verification)             │  ENGINE      │                │
│         │                                   │              │                │
│         │                                   └──────┬───────┘                │
│         │                                          │                        │
│         │                                          │ (approved plan)        │
│         │                                          ▼                        │
│         │                                   ┌──────────────┐                │
│         │                                   │              │                │
│         │◀──────────────────────────────────│  EXECUTION   │                │
│         │ (repair completion)               │  ENGINE      │                │
│         │                                   │              │                │
│         │                                   └──────┬───────┘                │
│         │                                          │                        │
│         │                                          │ (execution outcome)    │
│         │                                          ▼                        │
│         │                                   ┌──────────────┐                │
│         └──────────────────────────────────▶│              │                │
│              (learned improvements)         │  LEARNING    │                │
│                                             │  ENGINE      │                │
│                                             │              │                │
│                                             └──────────────┘                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  Routes, Request/Response schemas, Dependencies             │
│  Imports: application.services                              │
├─────────────────────────────────────────────────────────────┤
│                  Application Layer                          │
│  Services, Pipeline, Ports (interfaces)                     │
│  Imports: domain (models, value_objects, enums, events)     │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│  Models, Value Objects, Enums, Events                       │
│  Imports: NOTHING (pure domain)                             │
├─────────────────────────────────────────────────────────────┤
│                 Infrastructure Layer                        │
│  SQLAlchemy models, Repository implementations              │
│  Event bus, Cache, Plugins, External adapters               │
│  Imports: application.ports, domain (for types)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix C: Data Flow

```
                    ┌──────────────────────┐
                    │   Validation Engine  │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
   ┌────────────────┐ ┌───────────────┐ ┌────────────────┐
   │  Validation     │ │  Monitoring   │ │  Execution     │
   │  History        │ │  Engine       │ │  Engine        │
   └────────────────┘ └───────────────┘ └────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
   HistoryRecorded      Metrics Recorded    Permission Checked
   TrendComputed        Health Updated      Signature Verified
   FalsePositiveTracked                     Execution Starts
```

---

## Appendix D: Enum Reference

| Enum | Values |
|------|--------|
| ValidationStatus | pending, in_progress, completed, failed, timed_out |
| ValidationDecisionEnum | approved, rejected, conditional, pending_approval, needs_review, deferred, timed_out, escalated, expired, cancelled |
| ValidationSeverity | blocker, warning, info |
| ValidationCategory | safety, dependency, compatibility, resource, policy, security, rollback, cost |
| ApprovalLevel | auto, developer, maintainer, operations, administrator, emergency |
| ApprovalStatus | pending, approved, rejected, needs_review, deferred, timed_out, escalated, expired, cancelled |
| ExecutionPermissionStatus | granted, denied, expired, revoked |
| CascadeRisk | low, medium, high, critical |
| RollbackComplexity | low, medium, high, impossible |
| PolicyEnforcement | hard, soft |
| PolicyType | approval, cost, maintenance, production, security, business |
| BlockerType | rule_violation, policy_violation, approval_required, safety, resource, security |
| PolicyPackType | production, development, testing, infrastructure, financial, personal_assistant, experimental, custom |
| PluginType | infrastructure, cloud, database, financial, calendar, communication, custom |
| TrendType | risk, confidence, failure, approval, latency |

---

## Appendix E: Checklist Summary

| Category | Count |
|----------|-------|
| Domain Models | 26+ |
| Value Objects | 9 |
| Enums | 16 |
| Services | 20+ |
| Rules | 35+ |
| DB Tables | 11 |
| API Endpoints | 15 |
| Events | 21 |
| Tests | 200+ new |

---

**Status**: ARCHITECTURE REVIEW — Revised draft with improvements
**Next**: Implementation review, then Sprint 5A implementation
