# UAES v0.5 — Validation Engine Architecture Specification

> **Status**: FROZEN — Implementation-ready architecture document
> **Version**: 0.5.0
> **Date**: 2026-08-05
> **Owner**: ULTRON Core Team
> **Classification**: Internal Engineering Reference

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Responsibilities](#2-responsibilities)
3. [Architecture](#3-architecture)
4. [Domain Models](#4-domain-models)
5. [Value Objects](#5-value-objects)
6. [Enums](#6-enums)
7. [Repositories](#7-repositories)
8. [Services](#8-services)
9. [Validation Rules](#9-validation-rules)
10. [Approval Policy](#10-approval-policy)
11. [Validation Pipeline](#11-validation-pipeline)
12. [Database](#12-database)
13. [REST API](#13-rest-api)
14. [Events](#14-events)
15. [Integration](#15-integration)
16. [Failure Modes](#16-failure-modes)
17. [Security](#17-security)
18. [Performance](#18-performance)
19. [Testing Strategy](#19-testing-strategy)
20. [Definition of Done](#20-definition-of-done)

---

## 1. Purpose

### 1.1 Why It Exists

The ULTRON Autonomous Execution System (UAES) enables autonomous repair and remediation of infrastructure incidents. The Validation Engine is the **final safety gate** between the Planner (which generates repair plans) and the Execution Engine (which carries out those plans). Without the Validation Engine, the system would execute arbitrary repairs with no safety guarantee.

The Validation Engine answers a single question: **"Should ULTRON be allowed to execute this plan?"**

### 1.2 Problems It Solves

| Problem | Solution |
|---------|----------|
| Blind autonomous execution | Every plan passes through 17+ validation dimensions |
| No rollback safety net | Rollback feasibility assessment before execution |
| Insufficient human oversight | 5-level approval hierarchy with escalation |
| Unbounded blast radius | Dependency graph analysis with cascade risk scoring |
| Configuration drift | Compatibility checks across config, environment, and version |
| Resource exhaustion | Resource availability verification before execution |
| Compliance violations | Organizational policy enforcement with hard/soft modes |
| No audit trail | Immutable audit log with hash-chain integrity |
| Catastrophic actions | Hard blocks on destructive operations (delete production data, etc.) |
| Cost overruns | Budget compliance checks with threshold enforcement |

### 1.3 Defense-in-Depth Layers

The Validation Engine implements five nested defense layers, each providing an independent safety mechanism:

```
┌─────────────────────────────────────────────────────────────┐
│                    AUDIT LAYER                              │
│  Immutable log of every validation, decision, and action    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 APPROVAL LAYER                       │   │
│  │  Human approval with 5-level hierarchy               │   │
│  │  ┌───────────────────────────────────────────────┐   │   │
│  │  │              EVIDENCE LAYER                   │   │   │
│  │  │  Evidence-backed decisions with confidence    │   │   │
│  │  │  ┌────────────────────────────────────────┐   │   │   │
│  │  │  │           POLICY LAYER                 │   │   │
│  │  │  │  Organizational policies with          │   │   │
│  │  │  │  hard/soft enforcement                 │   │   │
│  │  │  │  ┌─────────────────────────────────┐   │   │   │   │
│  │  │  │  │         RULE LAYER              │   │   │   │   │
│  │  │  │  │  30+ configurable validation    │   │   │   │   │
│  │  │  │  │  rules across 8 categories     │   │   │   │   │
│  │  │  │  └─────────────────────────────────┘   │   │   │   │
│  │  │  └────────────────────────────────────────┘   │   │   │
│  │  └───────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Rule Layer**: Evaluates 30+ configurable rules across 8 categories. Rules produce blockers (hard stops) and warnings (advisory). Rules are evaluated sequentially; any blocker halts the pipeline.

**Policy Layer**: Enforces organizational policies. Policies are typed (approval, cost, maintenance, production, security, business) with hard enforcement (blocks execution) or soft enforcement (generates warnings).

**Evidence Layer**: Every decision is backed by evidence tuples `(source, key, value, confidence)`. Evidence is collected throughout the pipeline and stored for audit and debugging.

**Approval Layer**: 5-level human approval hierarchy (AUTO → DEVELOPER → MAINTAINER → OPERATIONS → ADMINISTRATOR). Emergency override with audit. Timeout-based escalation. Delegation rules.

**Audit Layer**: Immutable audit log with hash-chain integrity. Every validation, decision, approval, and permission change is recorded with actor, timestamp, IP, and details.

### 1.4 Position in UAES

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│              │     │                  │     │                  │     │                  │
│   Planner    │────▶│  Validation      │────▶│  Execution       │────▶│  Monitoring      │
│              │     │  Engine          │     │  Engine          │     │                  │
└──────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
       │                     │                        │                        │
       │  PlanGenerated      │  ValidationCompleted   │  ExecutionStarted      │
       └─────────────────────┘                        │  ExecutionCompleted    │
                                                      └────────────────────────┘
```

---

## 2. Responsibilities

### 2.1 Validation Dimensions

The Validation Engine evaluates every plan against 17+ dimensions. Each dimension produces evidence that feeds into the final decision.

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
backend/app/validation_engine/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── validation_request.py
│   │   ├── validation_result.py
│   │   ├── validation_decision.py
│   │   ├── validation_rule.py
│   │   ├── validation_policy.py
│   │   ├── validation_evidence.py
│   │   ├── validation_failure.py
│   │   ├── validation_warning.py
│   │   ├── approval_decision.py
│   │   ├── execution_permission.py
│   │   ├── execution_blocker.py
│   │   ├── safety_assessment.py
│   │   ├── compatibility_assessment.py
│   │   ├── rollback_assessment.py
│   │   ├── simulation_assessment.py
│   │   ├── dependency_assessment.py
│   │   ├── resource_assessment.py
│   │   ├── security_assessment.py
│   │   └── cost_assessment.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── confidence_score.py
│   │   ├── risk_score.py
│   │   ├── time_range.py
│   │   ├── threshold_range.py
│   │   ├── component_descriptor.py
│   │   ├── environment_descriptor.py
│   │   ├── version_constraint.py
│   │   ├── resource_quota.py
│   │   └── maintenance_window.py
│   ├── enums.py
│   └── events.py
├── application/
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── repositories.py
│   │   └── event_publisher.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── validation_service.py
│   │   ├── rule_engine.py
│   │   ├── policy_engine.py
│   │   ├── approval_engine.py
│   │   ├── dependency_analyzer.py
│   │   ├── compatibility_analyzer.py
│   │   ├── rollback_analyzer.py
│   │   ├── security_analyzer.py
│   │   ├── simulation_verifier.py
│   │   ├── environment_analyzer.py
│   │   ├── resource_analyzer.py
│   │   ├── decision_engine.py
│   │   └── summary_generator.py
│   └── pipeline/
│       ├── __init__.py
│       ├── validation_pipeline.py
│       └── stages.py
├── infrastructure/
│   ├── __init__.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── validation_request_model.py
│   │   │   ├── validation_result_model.py
│   │   │   ├── validation_failure_model.py
│   │   │   ├── validation_warning_model.py
│   │   │   ├── validation_evidence_model.py
│   │   │   ├── approval_decision_model.py
│   │   │   ├── execution_permission_model.py
│   │   │   └── audit_log_model.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── validation_repository.py
│   │   │   ├── rule_repository.py
│   │   │   ├── policy_repository.py
│   │   │   ├── evidence_repository.py
│   │   │   └── audit_repository.py
│   │   └── migrations/
│   │       └── versions/
│   │           └── 001_create_validation_tables.py
│   ├── event_bus/
│   │   ├── __init__.py
│   │   └── in_process_event_publisher.py
│   └── cache/
│       ├── __init__.py
│       └── rule_policy_cache.py
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── dependencies.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py
│   │       └── responses.py
│   └── __init__.py
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── __init__.py
    │   ├── test_validation_request.py
    │   ├── test_validation_result.py
    │   ├── test_validation_decision.py
    │   ├── test_validation_rule.py
    │   ├── test_validation_policy.py
    │   ├── test_validation_evidence.py
    │   ├── test_validation_failure.py
    │   ├── test_validation_warning.py
    │   ├── test_approval_decision.py
    │   ├── test_execution_permission.py
    │   ├── test_execution_blocker.py
    │   ├── test_safety_assessment.py
    │   ├── test_compatibility_assessment.py
    │   ├── test_rollback_assessment.py
    │   ├── test_simulation_assessment.py
    │   ├── test_dependency_assessment.py
    │   ├── test_resource_assessment.py
    │   ├── test_security_assessment.py
    │   ├── test_cost_assessment.py
    │   ├── test_confidence_score.py
    │   ├── test_risk_score.py
    │   ├── test_time_range.py
    │   ├── test_threshold_range.py
    │   ├── test_component_descriptor.py
    │   ├── test_environment_descriptor.py
    │   ├── test_version_constraint.py
    │   ├── test_resource_quota.py
    │   ├── test_maintenance_window.py
    │   ├── test_rule_engine.py
    │   ├── test_policy_engine.py
    │   ├── test_approval_engine.py
    │   ├── test_decision_engine.py
    │   └── test_summary_generator.py
    ├── integration/
    │   ├── __init__.py
    │   ├── test_validation_pipeline.py
    │   ├── test_validation_repository.py
    │   ├── test_rule_repository.py
    │   ├── test_policy_repository.py
    │   ├── test_evidence_repository.py
    │   ├── test_audit_repository.py
    │   ├── test_event_dispatch.py
    │   └── test_full_validation_flow.py
    ├── stress/
    │   ├── __init__.py
    │   ├── test_concurrent_validations.py
    │   └── test_timeout_handling.py
    └── chaos/
        ├── __init__.py
        ├── test_database_failure.py
        ├── test_rule_engine_failure.py
        ├── test_approval_timeout.py
        └── test_partial_validation.py
```

### 3.3 Clean Architecture / DDD Layers

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
│  Event bus, Cache, External adapters                        │
│  Imports: application.ports, domain (for types)             │
└─────────────────────────────────────────────────────────────┘
```

**Dependency Rules**:
- **Domain** → depends on nothing. Pure data structures, enums, and value objects.
- **Application** → depends only on Domain. Defines port interfaces (repository protocols, event publisher protocols). Services implement business logic.
- **Infrastructure** → depends on Application (ports) and Domain (types). Implements repository protocols, event publishing, caching.
- **API** → depends on Application. Defines HTTP routes, request/response schemas, dependency injection wiring.

---

## 4. Domain Models

All domain models are Pydantic `BaseModel` with `frozen=True` and `model_config = ConfigDict(use_enum_values=True)`. Mutations use `model_copy(update={...})`.

### 4.1 ValidationRequest

Entry point from the Planner. Immutable request to validate a plan.

```python
class ValidationRequest(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    request_id: str                              # UUID, auto-generated
    plan_id: str                                 # Reference to the plan being validated
    incident_id: str | None                      # Associated incident (if any)
    plan_json: dict[str, Any]                    # Serialized plan for validation
    environment: str                             # "development" | "staging" | "production"
    requested_by: str                            # Actor who requested validation
    requested_at: datetime                       # When the request was made
    priority: int = 0                            # Higher = validate first
    timeout_seconds: int = 300                   # Validation timeout (default 5min)
    metadata: dict[str, Any] = {}                # Arbitrary metadata
```

### 4.2 ValidationDecision

Enum-based decision outcome. This is the final verdict of the validation pipeline.

```python
class ValidationDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision: ValidationDecisionEnum              # APPROVED, REJECTED, CONDITIONAL, PENDING_APPROVAL, EXPIRED
    decision_reason: str                          # Human-readable reason
    decided_at: datetime                          # When the decision was made
    decided_by: str                               # "system" for auto, user ID for human
    conditions: list[str] = []                    # Conditions for CONDITIONAL approval
    expiration_at: datetime | None = None         # When the decision expires
    validation_duration_ms: float                 # How long validation took
```

### 4.3 ValidationRule

Configurable rule with conditions. Rules are the atomic unit of validation logic.

```python
class ValidationRule(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rule_id: str                                  # e.g., "SAFETY_001"
    rule_code: str                                # e.g., "SAFETY_001"
    name: str                                     # e.g., "Block Database Restart During Migration"
    description: str                              # What this rule checks
    category: ValidationCategory                  # SAFETY, DEPENDENCY, COMPATIBILITY, etc.
    severity: ValidationSeverity                  # BLOCKER, WARNING, INFO
    enabled: bool = True                          # Can be disabled without removing
    conditions: list[dict[str, Any]] = []         # JSON-logic conditions
    message_on_pass: str = ""                     # Message when rule passes
    message_on_fail: str = ""                     # Message when rule fails
    suggested_fix: str = ""                       # Suggested remediation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.4 ValidationPolicy

Organizational policy. Policies are higher-level than rules and enforce business/organizational constraints.

```python
class ValidationPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    policy_id: str                                # e.g., "POLICY_MAINT_001"
    name: str                                     # e.g., "Production Maintenance Window"
    description: str                              # What this policy enforces
    policy_type: PolicyType                       # APPROVAL, COST, MAINTENANCE, PRODUCTION, SECURITY, BUSINESS
    enforcement: PolicyEnforcement                 # HARD (blocks) or SOFT (warns)
    enabled: bool = True
    conditions: list[dict[str, Any]] = []         # JSON-logic conditions
    applicable_environments: list[str] = []       # Empty = all environments
    message_on_pass: str = ""
    message_on_fail: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.5 ValidationEvidence

Evidence tuple. Every decision is backed by evidence. Evidence is the audit trail of what was checked and what was found.

```python
class ValidationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    evidence_id: str                              # UUID, auto-generated
    result_id: str                                # FK to ValidationResult
    evidence_type: str                            # "rule_result", "assessment", "external_check"
    source: str                                   # Which service produced this evidence
    key: str                                      # What was checked (e.g., "cpu_availability")
    value: Any                                    # What was found
    confidence: ConfidenceScore                   # 0.0-1.0 confidence in this evidence
    metadata: dict[str, Any] = {}                 # Additional context
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.6 ValidationFailure

Blocker. A failure that prevents execution. Failures are produced by rules with BLOCKER severity.

```python
class ValidationFailure(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    failure_id: str                               # UUID, auto-generated
    result_id: str                                # FK to ValidationResult
    rule_id: str                                  # FK to ValidationRule
    rule_code: str                                # e.g., "SAFETY_001"
    rule_name: str                                # e.g., "Block Database Restart During Migration"
    category: ValidationCategory                  # Which category
    severity: ValidationSeverity                  # Always BLOCKER for failures
    reason: str                                   # Why this failed
    suggested_fix: str                            # How to fix it
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.7 ValidationWarning

Non-blocking advisory. Warnings inform but do not block execution.

```python
class ValidationWarning(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    warning_id: str                               # UUID, auto-generated
    result_id: str                                # FK to ValidationResult
    rule_id: str                                  # FK to ValidationRule
    rule_code: str                                # e.g., "ROLLBACK_003"
    rule_name: str                                # e.g., "Low Rollback Success Rate"
    category: ValidationCategory                  # Which category
    severity: ValidationSeverity                  # Always WARNING
    message: str                                  # What was observed
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.8 ApprovalDecision

Human approval record. Tracks who approved/rejected what, when, and with what conditions.

```python
class ApprovalDecision(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    decision_id: str                              # UUID, auto-generated
    request_id: str                               # FK to ValidationRequest
    result_id: str | None                         # FK to ValidationResult (if decision made)
    plan_id: str                                  # FK to the plan
    decision: ApprovalStatus                      # PENDING, APPROVED, REJECTED, ESCALATED, EXPIRED
    decided_by: str                               # User ID of approver
    reason: str                                   # Why they approved/rejected
    conditions: list[str] = []                    # Conditions for conditional approval
    approval_level: ApprovalLevel                 # Who can approve at this level
    expires_at: datetime                          # When this approval expires
    decided_at: datetime | None = None            # When the decision was made
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.9 ExecutionPermission

Grants or denies execution. This is the final artifact that the Execution Engine checks before running a plan.

```python
class ExecutionPermission(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    permission_id: str                            # UUID, auto-generated
    plan_id: str                                  # FK to the plan
    result_id: str                                # FK to ValidationResult
    granted: bool                                 # True = can execute, False = blocked
    granted_by: str                               # "system" for auto, user ID for human
    granted_at: datetime                          # When permission was granted
    expires_at: datetime                          # When permission expires
    conditions: list[str] = []                    # Conditions that must be met
    revocation_reason: str | None = None          # Why permission was revoked (if revoked)
    revoked_at: datetime | None = None            # When permission was revoked
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.10 ExecutionBlocker

Explicit execution block. Produced when validation fails. The Execution Engine checks for active blockers before executing.

```python
class ExecutionBlocker(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    blocker_id: str                               # UUID, auto-generated
    plan_id: str                                  # FK to the plan
    result_id: str                                # FK to ValidationResult
    blocker_type: BlockerType                     # RULE_VIOLATION, POLICY_VIOLATION, etc.
    reason: str                                   # Why execution is blocked
    rule_code: str | None = None                  # Which rule caused the block
    policy_id: str | None = None                  # Which policy caused the block
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None           # When the blocker was resolved
```

### 4.11 SafetyAssessment

Risk, confidence, blast radius, and historical failure analysis.

```python
class SafetyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    risk_score: RiskScore                         # 0-100, computed from multiple factors
    confidence_score: ConfidenceScore             # 0.0-1.0, how confident in this assessment
    blast_radius: int                             # Number of components affected
    historical_failures: int                      # How many times similar repairs failed
    is_catastrophic: bool                         # risk_score > 95
    requires_human_approval: bool                 # Based on risk threshold
    assessment_summary: str                       # Human-readable summary
    factors: dict[str, float] = {}                # Individual risk factors
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.12 CompatibilityAssessment

Configuration, environment, and version compatibility.

```python
class CompatibilityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    config_compatible: bool                       # Configuration conflict detected?
    environment_compatible: bool                  # Environment mismatch?
    version_compatible: bool                      # Version incompatibility?
    config_conflicts: list[str] = []              # Specific config conflicts found
    environment_mismatches: list[str] = []        # Specific env mismatches found
    version_incompatibilities: list[str] = []     # Specific version issues found
    pre_release_components: list[str] = []        # Components using pre-release versions
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.13 RollbackAssessment

Rollback feasibility, complexity, and success rate.

```python
class RollbackAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    rollback_available: bool                      # Is a rollback plan available?
    automatic_rollback: bool                      # Can rollback be done automatically?
    rollback_tested: bool                         # Has this rollback been tested?
    rollback_success_rate: float                  # 0.0-1.0, historical success rate
    rollback_complexity: RollbackComplexity       # LOW, MEDIUM, HIGH, IMPOSSIBLE
    data_loss_risk: bool                          # Will rollback cause data loss?
    estimated_rollback_time_seconds: int          # How long rollback takes
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.14 SimulationAssessment

Simulation outcome and pre/postcondition verification.

```python
class SimulationAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    simulation_performed: bool                    # Was a simulation run?
    simulation_outcome: str                       # "success", "failure", "timeout", "not_performed"
    preconditions_met: bool                       # Were preconditions satisfied?
    postconditions_met: bool                      # Were postconditions satisfied?
    simulation_duration_ms: float                 # How long the simulation took
    simulation_errors: list[str] = []             # Errors during simulation
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.15 DependencyAssessment

Graph traversal, blast radius calculation, and cascade risk.

```python
class DependencyAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    direct_dependencies: list[str] = []           # Services this plan directly affects
    reverse_dependencies: list[str] = []          # Services that depend on affected services
    blast_radius: int                             # Total components in impact zone
    cascade_risk: CascadeRisk                     # LOW, MEDIUM, HIGH, CRITICAL
    critical_path_affected: bool                  # Is a critical path service affected?
    cross_boundary_impact: bool                   # Does impact cross bounded context boundaries?
    dependent_service_count: int                  # How many services depend on affected services
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.16 ResourceAssessment

CPU, memory, disk, and network availability.

```python
class ResourceAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    cpu_available_percent: float                  # Current CPU availability
    memory_available_mb: float                    # Current memory availability
    disk_available_gb: float                      # Current disk availability
    network_impact: str                           # "low", "medium", "high"
    resource_sufficient: bool                     # Are resources sufficient for this repair?
    estimated_downtime_seconds: int               # Estimated downtime for this repair
    resource_conflicts: list[str] = []            # Specific resource conflicts
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.17 SecurityAssessment

Permissions, authentication, and audit requirements.

```python
class SecurityAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    auth_valid: bool                              # Is the auth token valid?
    permissions_sufficient: bool                  # Does the actor have required permissions?
    elevated_permissions_required: bool           # Does this action need elevated permissions?
    audit_trail_complete: bool                    # Is the audit trail complete?
    security_violations: list[str] = []           # Specific security violations found
    required_roles: list[str] = []                # Roles required for this action
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.18 CostAssessment

Operational cost, human effort, and budget compliance.

```python
class CostAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, use_enum_values=True)

    estimated_cost_usd: float                     # Estimated operational cost
    human_effort_hours: float                     # Estimated human effort required
    budget_remaining_usd: float                   # Remaining budget for this period
    budget_compliant: bool                        # Is this within budget?
    cost_breakdown: dict[str, float] = {}         # Itemized cost breakdown
    cost_approval_required: bool                  # Does this exceed budget threshold?
    assessment_summary: str = ""                  # Human-readable summary
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 5. Value Objects

Value objects are immutable, equality-by-value types. They encapsulate domain concepts with built-in validation.

### 5.1 ConfidenceScore

```python
class ConfidenceScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: float                                  # 0.0 to 1.0

    @field_validator("value")
    @classmethod
    def validate_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"ConfidenceScore must be between 0.0 and 1.0, got {v}")
        return v

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

### 5.2 RiskScore

```python
class RiskScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: int                                    # 0 to 100

    @field_validator("value")
    @classmethod
    def validate_range(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError(f"RiskScore must be between 0 and 100, got {v}")
        return v

    @property
    def is_low(self) -> bool:
        return self.value < 30

    @property
    def is_medium(self) -> bool:
        return 30 <= self.value < 70

    @property
    def is_high(self) -> bool:
        return 70 <= self.value < 95

    @property
    def is_catastrophic(self) -> bool:
        return self.value >= 95
```

### 5.3 TimeRange

```python
class TimeRange(BaseModel):
    model_config = ConfigDict(frozen=True)

    start: datetime
    end: datetime

    @field_validator("end")
    @classmethod
    def validate_after_start(cls, v: datetime, info) -> datetime:
        start = info.data.get("start")
        if start and v <= start:
            raise ValueError("end must be after start")
        return v

    @property
    def duration_seconds(self) -> float:
        return (self.end - self.start).total_seconds()

    def contains(self, dt: datetime) -> bool:
        return self.start <= dt <= self.end
```

### 5.4 ThresholdRange

```python
class ThresholdRange(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_value: float
    max_value: float

    @field_validator("max_value")
    @classmethod
    def validate_max_gte_min(cls, v: float, info) -> float:
        min_val = info.data.get("min_value")
        if min_val is not None and v < min_val:
            raise ValueError(f"max_value ({v}) must be >= min_value ({min_val})")
        return v

    def contains(self, value: float) -> bool:
        return self.min_value <= value <= self.max_value
```

### 5.5 ComponentDescriptor

```python
class ComponentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str                                     # Component name (e.g., "api-gateway")
    component_type: str                           # "service", "database", "cache", "queue"
    environment: str                              # "development", "staging", "production"
    version: str | None = None                    # Current version
    health_status: str = "unknown"                # "healthy", "degraded", "unhealthy"
    metadata: dict[str, Any] = {}
```

### 5.6 EnvironmentDescriptor

```python
class EnvironmentDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str                                     # "development", "staging", "production"
    is_production: bool                           # Convenience flag
    allowed_actions: list[str] = []               # Actions allowed in this environment
    restricted_actions: list[str] = []            # Actions restricted in this environment
    required_approvals: list[str] = []            # Approvals required in this environment
    maintenance_window: MaintenanceWindow | None = None
```

### 5.7 VersionConstraint

```python
class VersionConstraint(BaseModel):
    model_config = ConfigDict(frozen=True)

    component: str                                # Component name
    constraint: str                               # Semver constraint (e.g., ">=1.0.0,<2.0.0")
    current_version: str | None = None            # Currently deployed version
    required_version: str | None = None           # Required version for this plan

    def is_satisfied_by(self, version: str) -> bool:
        # Semver constraint checking logic
        ...
```

### 5.8 ResourceQuota

```python
class ResourceQuota(BaseModel):
    model_config = ConfigDict(frozen=True)

    cpu_percent: ThresholdRange                   # CPU availability threshold
    memory_mb: ThresholdRange                     # Memory availability threshold (MB)
    disk_gb: ThresholdRange                       # Disk availability threshold (GB)
    network_impact: str                           # "low", "medium", "high" max allowed

    @classmethod
    def production_defaults(cls) -> ResourceQuota:
        return cls(
            cpu_percent=ThresholdRange(min_value=20.0, max_value=100.0),
            memory_mb=ThresholdRange(min_value=512.0, max_value=100000.0),
            disk_gb=ThresholdRange(min_value=1.0, max_value=10000.0),
            network_impact="medium",
        )
```

### 5.9 MaintenanceWindow

```python
class MaintenanceWindow(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str                                     # e.g., "Weekly Maintenance"
    schedule: str                                 # Cron expression or "always", "never"
    timezone: str = "UTC"
    allowed_actions: list[str] = []               # Actions allowed during window
    blocked_actions: list[str] = []               # Actions blocked outside window
    is_active: bool = False                       # Is the window currently active?

    def is_now_in_window(self, dt: datetime | None = None) -> bool:
        # Check if current time (or provided time) is within window
        ...
```

---

## 6. Enums

All enums use `StrEnum` for JSON serialization compatibility with `use_enum_values=True`.

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
    EXPIRED = "expired"


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
    ESCALATED = "escalated"
    EXPIRED = "expired"


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
```

---

## 7. Repositories

Repository interfaces are defined as `Protocol` classes in `application/ports/repositories.py`. Implementations live in `infrastructure/persistence/repositories/`.

All repositories follow the existing codebase convention:
- Async methods
- `flush()` after writes (never `commit()` — callers commit)
- Return domain models, not ORM models
- Use dependency injection via `__init__`

### 7.1 ValidationRepository

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

### 7.2 RuleRepository

```python
class RuleRepository(Protocol):
    async def get_all_rules(self) -> list[ValidationRule]: ...
    async def get_rules_by_category(self, category: ValidationCategory) -> list[ValidationRule]: ...
    async def get_enabled_rules(self) -> list[ValidationRule]: ...
    async def get_rule_by_code(self, rule_code: str) -> ValidationRule | None: ...
    async def save_rule(self, rule: ValidationRule) -> None: ...
```

### 7.3 PolicyRepository

```python
class PolicyRepository(Protocol):
    async def get_all_policies(self) -> list[ValidationPolicy]: ...
    async def get_policies_by_type(self, policy_type: PolicyType) -> list[ValidationPolicy]: ...
    async def get_active_policies(self) -> list[ValidationPolicy]: ...
    async def get_policy_by_id(self, policy_id: str) -> ValidationPolicy | None: ...
    async def save_policy(self, policy: ValidationPolicy) -> None: ...
```

### 7.4 EvidenceRepository

```python
class EvidenceRepository(Protocol):
    async def save_evidence(self, evidence: ValidationEvidence) -> None: ...
    async def save_evidence_batch(self, evidence_list: list[ValidationEvidence]) -> None: ...
    async def get_evidence_by_result(self, result_id: str) -> list[ValidationEvidence]: ...
```

### 7.5 AuditRepository

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

---

## 8. Services

### 8.1 Service Overview

| Service | Location | Responsibility |
|---------|----------|---------------|
| ValidationService | `application/services/validation_service.py` | Orchestrator. 12-stage pipeline. |
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
| DecisionEngine | `application/services/decision_engine.py` | Aggregates all assessments, makes final decision. |
| SummaryGenerator | `application/services/summary_generator.py` | Human-readable validation summary. |

### 8.2 ValidationService

The orchestrator. Receives a `ValidationRequest`, runs it through the 12-stage pipeline, and produces a `ValidationDecision`.

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
        validation_repository: ValidationRepository,
        evidence_repository: EvidenceRepository,
        audit_repository: AuditRepository,
        event_publisher: EventPublisher,
    ) -> None: ...

    async def validate(self, request: ValidationRequest) -> ValidationDecision:
        """Run the 12-stage validation pipeline."""
        ...

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

### 8.3 RuleEngine

Evaluates all applicable rules against a plan. Produces blockers and warnings.

```python
class RuleEngine:
    def __init__(
        self,
        *,
        rule_repository: RuleRepository,
        cache: RulePolicyCache,
    ) -> None: ...

    async def evaluate(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
    ) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
        """Evaluate all enabled rules. Returns (failures, warnings)."""
        ...
```

### 8.4 PolicyEngine

Evaluates all applicable policies. Enforces hard (block) and soft (warn) policies.

```python
class PolicyEngine:
    def __init__(
        self,
        *,
        policy_repository: PolicyRepository,
        cache: RulePolicyCache,
    ) -> None: ...

    async def evaluate(
        self,
        request: ValidationRequest,
        assessments: dict[str, Any],
    ) -> tuple[list[ValidationFailure], list[ValidationWarning]]:
        """Evaluate all active policies. Returns (failures, warnings)."""
        ...
```

### 8.5 ApprovalEngine

Determines the required approval level based on risk, environment, and severity. Manages the approval workflow.

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
        is_production: bool,
    ) -> ApprovalLevel:
        """Determine the required approval level."""
        ...

    async def check_approval_status(
        self,
        request_id: str,
        required_level: ApprovalLevel,
    ) -> ApprovalDecision | None:
        """Check if required approval exists and is valid."""
        ...

    async def escalate(
        self,
        current_level: ApprovalLevel,
        request_id: str,
    ) -> ApprovalLevel:
        """Escalate to next approval level."""
        ...
```

### 8.6 DependencyAnalyzer

Graph traversal and blast radius calculation.

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
    ) -> DependencyAssessment:
        """Analyze dependency impact of the plan."""
        ...

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

### 8.7 CompatibilityAnalyzer

Configuration, environment, and version compatibility checks.

```python
class CompatibilityAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> CompatibilityAssessment:
        """Check config, environment, and version compatibility."""
        ...

    async def check_config_compatibility(
        self,
        plan: dict[str, Any],
        environment: str,
    ) -> list[str]: ...

    async def check_environment_compatibility(
        self,
        plan: dict[str, Any],
        environment: str,
    ) -> list[str]: ...

    async def check_version_compatibility(
        self,
        plan: dict[str, Any],
    ) -> list[str]: ...
```

### 8.8 RollbackAnalyzer

Rollback feasibility assessment.

```python
class RollbackAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> RollbackAssessment:
        """Assess rollback feasibility."""
        ...

    def _calculate_success_rate(
        self,
        component: str,
        action_type: str,
    ) -> float: ...

    def _assess_complexity(
        self,
        has_data_migration: bool,
        has_config_change: bool,
        has_service_restart: bool,
    ) -> RollbackComplexity: ...
```

### 8.9 SecurityAnalyzer

Permission, auth, and audit checks.

```python
class SecurityAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> SecurityAssessment:
        """Check security constraints."""
        ...

    async def check_permissions(
        self,
        actor: str,
        required_roles: list[str],
    ) -> bool: ...

    async def check_audit_trail(
        self,
        plan_id: str,
    ) -> bool: ...
```

### 8.10 SimulationVerifier

Validates simulation results.

```python
class SimulationVerifier:
    async def verify(
        self,
        request: ValidationRequest,
    ) -> SimulationAssessment:
        """Verify simulation results if available."""
        ...

    def _check_preconditions(
        self,
        simulation_result: dict[str, Any],
    ) -> bool: ...

    def _check_postconditions(
        self,
        simulation_result: dict[str, Any],
    ) -> bool: ...
```

### 8.11 EnvironmentAnalyzer

Environment-specific constraints.

```python
class EnvironmentAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> dict[str, Any]:
        """Analyze environment-specific constraints."""
        ...

    async def is_maintenance_window(
        self,
        environment: str,
    ) -> bool: ...

    async def get_environment_policy(
        self,
        environment: str,
    ) -> EnvironmentDescriptor: ...
```

### 8.12 ResourceAnalyzer

CPU, memory, disk, and network checks.

```python
class ResourceAnalyzer:
    async def analyze(
        self,
        request: ValidationRequest,
    ) -> ResourceAssessment:
        """Check resource availability."""
        ...

    async def get_current_resources(self) -> dict[str, float]:
        """Get current resource utilization."""
        ...

    def _estimate_downtime(
        self,
        plan: dict[str, Any],
    ) -> int: ...
```

### 8.13 DecisionEngine

Aggregates all assessments and makes the final decision.

```python
class DecisionEngine:
    def decide(
        self,
        request: ValidationRequest,
        safety: SafetyAssessment,
        dependency: DependencyAssessment,
        compatibility: CompatibilityAssessment,
        rollback: RollbackAssessment,
        simulation: SimulationAssessment,
        resource: ResourceAssessment,
        security: SecurityAssessment,
        cost: CostAssessment,
        failures: list[ValidationFailure],
        warnings: list[ValidationWarning],
        approval_level: ApprovalLevel,
    ) -> ValidationDecision:
        """Make the final validation decision."""
        ...

    def _has_blockers(self, failures: list[ValidationFailure]) -> bool:
        return len(failures) > 0

    def _needs_approval(self, level: ApprovalLevel) -> bool:
        return level != ApprovalLevel.AUTO
```

### 8.14 SummaryGenerator

Human-readable validation summary.

```python
class SummaryGenerator:
    def generate(
        self,
        request: ValidationRequest,
        decision: ValidationDecision,
        safety: SafetyAssessment,
        dependency: DependencyAssessment,
        compatibility: CompatibilityAssessment,
        rollback: RollbackAssessment,
        simulation: SimulationAssessment,
        resource: ResourceAssessment,
        security: SecurityAssessment,
        cost: CostAssessment,
        failures: list[ValidationFailure],
        warnings: list[ValidationWarning],
    ) -> str:
        """Generate a human-readable validation summary."""
        ...
```

---

## 9. Validation Rules

### 9.1 Safety Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| SAFETY_001 | Block Database Restart During Migration | BLOCKER | Plan restarts database AND active migration detected |
| SAFETY_002 | Block Redis Restart During Cache Migration | BLOCKER | Plan restarts Redis AND cache migration in progress |
| SAFETY_003 | Block Production Data Deletion | BLOCKER | Plan deletes data AND environment is production |
| SAFETY_004 | Block Deploy If Tests Failed | BLOCKER | Plan deploys AND tests failed in pipeline |
| SAFETY_005 | Block Low-Confidence Repair in Production | BLOCKER | Confidence < 0.3 AND environment is production |
| SAFETY_006 | Block Restart Without Rollback Plan | BLOCKER | Plan restarts service AND no rollback plan available |
| SAFETY_007 | Block Catastrophic Risk Repairs | BLOCKER | Risk score > 95 |
| SAFETY_008 | Block Multi-Component Repairs (>5) | BLOCKER | Blast radius > 5 components |

### 9.2 Dependency Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| DEPENDENCY_001 | Block Critical Path Service Impact | BLOCKER | Critical path service affected |
| DEPENDENCY_002 | Block Critical Cascade Risk | BLOCKER | Cascade risk is CRITICAL |
| DEPENDENCY_003 | Require Staging Validation (>3 Components) | WARNING | >3 components affected AND no staging validation |
| DEPENDENCY_004 | Block Cross-Boundary Impact | BLOCKER | Impact crosses bounded context boundaries |
| DEPENDENCY_005 | Require Rollback for High-Dep Services | BLOCKER | Service has >100 dependents AND no rollback plan |

### 9.3 Compatibility Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| COMPAT_001 | Block Configuration Conflict | BLOCKER | Configuration conflict detected |
| COMPAT_002 | Block Environment Mismatch | BLOCKER | Environment mismatch detected |
| COMPAT_003 | Block Version Incompatibility | BLOCKER | Version incompatibility detected |
| COMPAT_004 | Require Manual Review for Pre-Release | WARNING | Pre-release version in plan |
| COMPAT_005 | Block Dependency Version Constraint Violation | BLOCKER | Dependency version constraint violated |

### 9.4 Resource Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| RESOURCE_001 | Block Low CPU Availability | BLOCKER | CPU availability < 20% |
| RESOURCE_002 | Block Low Memory Availability | BLOCKER | Memory availability < 512MB |
| RESOURCE_003 | Block Low Disk Space | BLOCKER | Disk space < 1GB |
| RESOURCE_004 | Block High Network Impact During Peak | BLOCKER | Network impact is HIGH AND during peak hours |
| RESOURCE_005 | Block Downtime Exceeding Maintenance Window | BLOCKER | Estimated downtime > maintenance window |

### 9.5 Policy Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| POLICY_001 | Production Changes Require Maintainer Approval | BLOCKER | Environment is production AND no maintainer approval |
| POLICY_002 | Critical Severity Requires Administrator Approval | BLOCKER | Severity is critical AND no admin approval |
| POLICY_003 | Operations Outside Maintenance Window Blocked | BLOCKER | Production AND outside maintenance window |
| POLICY_004 | Cost Impact Exceeding Budget Requires Approval | BLOCKER | Cost > budget threshold AND no approval |
| POLICY_005 | Emergency Override Requires Emergency Role | BLOCKER | Emergency override AND actor lacks emergency role |
| POLICY_006 | Database Changes Require DBA Approval | BLOCKER | Database component affected AND no DBA approval |
| POLICY_007 | Redis Changes Require Cache Team Approval | BLOCKER | Redis component affected AND no cache team approval |
| POLICY_008 | Network Changes Require Network Team Approval | BLOCKER | Network component affected AND no network team approval |

### 9.6 Security Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| SECURITY_001 | Block Expired Auth Token | BLOCKER | Auth token expired |
| SECURITY_002 | Block Insufficient Role | BLOCKER | User lacks required role |
| SECURITY_003 | Block Elevated Permission Without Authorization | BLOCKER | Action requires elevated permissions AND not authorized |
| SECURITY_004 | Block Incomplete Audit Trail | BLOCKER | Audit trail incomplete for this action |

### 9.7 Rollback Rules

| Code | Name | Severity | Condition |
|------|------|----------|-----------|
| ROLLBACK_001 | Block if Rollback Unavailable and Risk > Medium | BLOCKER | No rollback available AND risk > 50 |
| ROLLBACK_002 | Block Impossible Rollback | BLOCKER | Rollback complexity is IMPOSSIBLE |
| ROLLBACK_003 | Warn Low Rollback Success Rate | WARNING | Rollback success rate < 80% |
| ROLLBACK_004 | Block Data Loss Risk During Rollback | BLOCKER | Data loss risk detected during rollback |

---

## 10. Approval Policy

### 10.1 Approval Hierarchy

```
Level 6: EMERGENCY    ── Any env, emergency override with full audit
Level 5: ADMINISTRATOR ── Production, risk >= 90, or catastrophic severity
Level 4: OPERATIONS    ── Production, risk < 90, or critical severity
Level 3: MAINTAINER    ── Production, risk < 70
Level 2: DEVELOPER     ── Any env, risk < 50, confidence > 0.6
Level 1: AUTO          ── Dev/staging only, risk < 30, confidence > 0.8, rollback available
```

### 10.2 Approval Level Determination

```python
def determine_approval_level(
    risk_score: RiskScore,
    environment: str,
    severity: str,
    confidence: ConfidenceScore,
    rollback_available: bool,
) -> ApprovalLevel:
    is_production = environment == "production"

    # EMERGENCY override (explicit request)
    # Checked separately via emergency_override parameter

    # AUTO: dev/staging, low risk, high confidence, rollback available
    if (
        not is_production
        and risk_score.value < 30
        and confidence.value > 0.8
        and rollback_available
    ):
        return ApprovalLevel.AUTO

    # DEVELOPER: any env, moderate risk, decent confidence
    if risk_score.value < 50 and confidence.value > 0.6:
        return ApprovalLevel.DEVELOPER

    # MAINTAINER: production, moderate-high risk
    if is_production and risk_score.value < 70:
        return ApprovalLevel.MAINTAINER

    # OPERATIONS: production, high risk, or critical severity
    if is_production and (risk_score.value < 90 or severity == "critical"):
        return ApprovalLevel.OPERATIONS

    # ADMINISTRATOR: production, very high risk, or catastrophic
    return ApprovalLevel.ADMINISTRATOR
```

### 10.3 Escalation Matrix

| Current Level | Escalates To | Trigger |
|---------------|-------------|---------|
| AUTO | DEVELOPER | Risk increases or confidence drops |
| DEVELOPER | MAINTAINER | Environment is production OR risk >= 50 |
| MAINTAINER | OPERATIONS | Risk >= 70 OR severity is critical |
| OPERATIONS | ADMINISTRATOR | Risk >= 90 OR severity is catastrophic |
| ADMINISTRATOR | EMERGENCY | System-wide incident OR emergency override |

### 10.4 Timeout Rules

| Context | Timeout | Action on Timeout |
|---------|---------|------------------|
| Default (any level) | 24 hours | Auto-escalate to next level |
| Production environment | 4 hours | Auto-escalate to next level |
| Critical severity | 1 hour | Auto-escalate to next level |
| Emergency override | 30 minutes | Auto-expire, full audit |

### 10.5 Delegation Rules

- **AUTO**: No delegation needed (system-authorized)
- **DEVELOPER**: Can be delegated to any user with `developer` role
- **MAINTAINER**: Can be delegated to any user with `maintainer` role OR higher
- **OPERATIONS**: Can be delegated to any user with `operations` role OR higher
- **ADMINISTRATOR**: Cannot be delegated (must be explicit approval)
- **EMERGENCY**: Cannot be delegated (must be explicit approval with audit)

### 10.6 Conditional Approval

Conditional approvals attach conditions that must be met before execution:

```python
# Example conditions
conditions = [
    "monitor_cpu_during_execution",
    "rollback_plan_must_be_tested",
    "notify_operations_channel",
    "execute_during_maintenance_window_only",
]
```

The Execution Engine checks all conditions before executing. If any condition is unmet, execution is blocked.

---

## 11. Validation Pipeline

### 11.1 Pipeline Overview

The Validation Pipeline is a 12-stage sequential pipeline. Each stage produces evidence and assessments that feed into subsequent stages. The pipeline halts early if a BLOCKER failure is detected.

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
│  Stage 12: Decision Engine                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Stage Descriptions

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
| 12. Decision Engine | All assessments + failures + warnings | `ValidationDecision` | DecisionEngine |

### 11.3 Happy Path (Auto-Approved)

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
   │                           │ └─ Stage 12: DECIDE         │
   │                           │                              │
   │                           │ Decision: APPROVED          │
   │                           │ Permission: GRANTED         │
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

### 11.4 Requires Approval Path

```
Planner                  Validation Engine              Approver
   │                           │                              │
   │  PlanGenerated            │                              │
   │──────────────────────────▶│                              │
   │                           │                              │
   │                           │ (Pipeline runs...)           │
   │                           │ Stage 12: PENDING_APPROVAL   │
   │                           │                              │
   │  ValidationCompleted      │                              │
   │  (PENDING_APPROVAL)       │                              │
   │◀──────────────────────────│                              │
   │                           │                              │
   │                           │  ValidationApprovalRequired  │
   │                           │─────────────────────────────▶│
   │                           │                              │
   │                           │                              │ Review
   │                           │                              │ Approve/Reject
   │                           │                              │
   │                           │  ValidationApprovalGranted   │
   │                           │◀─────────────────────────────│
   │                           │                              │
   │                           │ Permission: GRANTED          │
   │                           │                              │
   │  ValidationCompleted      │                              │
   │  (APPROVED)               │                              │
   │◀──────────────────────────│                              │
```

### 11.5 Rejected Path

```
Planner                  Validation Engine
   │                           │
   │  PlanGenerated            │
   │──────────────────────────▶│
   │                           │
   │                           │ (Pipeline runs...)
   │                           │ Stage 10: SAFETY_007 fires
   │                           │   Risk score > 95
   │                           │
   │                           │ Blocker detected, halt pipeline
   │                           │
   │                           │ Decision: REJECTED
   │                           │ Permission: DENIED
   │                           │
   │  ValidationCompleted      │
   │  (REJECTED)               │
   │◀──────────────────────────│
   │                           │
   │  ValidationBlockerDetected│
   │  (SAFETY_007)             │
   │◀──────────────────────────│
```

### 11.6 Conditional Approval Path

```
Planner                  Validation Engine              Approver
   │                           │                              │
   │  PlanGenerated            │                              │
   │──────────────────────────▶│                              │
   │                           │                              │
   │                           │ (Pipeline runs...)           │
   │                           │ Stage 12: CONDITIONAL        │
   │                           │   Conditions:                │
   │                           │   - monitor_during_execution │
   │                           │   - rollback_tested          │
   │                           │                              │
   │                           │  ValidationApprovalRequired  │
   │                           │─────────────────────────────▶│
   │                           │                              │
   │                           │                              │ Approve with conditions
   │                           │  ValidationApprovalGranted   │
   │                           │◀─────────────────────────────│
   │                           │                              │
   │                           │ Permission: GRANTED          │
   │                           │   Conditions: [...]          │
   │                           │                              │
   │  ValidationCompleted      │
   │  (CONDITIONAL)            │
   │◀──────────────────────────│
```

---

## 12. Database

### 12.1 Schema Overview

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
│                             └── uaes_validation_audit_log        │
└─────────────────────────────────────────────────────────────────┘
```

### 12.2 Tables

#### uaes_validation_requests

```sql
CREATE TABLE uaes_validation_requests (
    request_id          VARCHAR(36) PRIMARY KEY,
    plan_id             VARCHAR(36) NOT NULL,
    incident_id         VARCHAR(36),
    request_json        TEXT NOT NULL,
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
    rules_evaluated         INTEGER NOT NULL DEFAULT 0,
    rules_passed            INTEGER NOT NULL DEFAULT 0,
    rules_failed            INTEGER NOT NULL DEFAULT 0,
    approval_required       BOOLEAN NOT NULL DEFAULT FALSE,
    approval_level          VARCHAR(30),
    validated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validation_duration_ms  FLOAT NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uvr_result_plan_id ON uaes_validation_results(plan_id);
CREATE INDEX idx_uvr_result_incident_id ON uaes_validation_results(incident_id);
CREATE INDEX idx_uvr_result_decision ON uaes_validation_results(decision);
CREATE INDEX idx_uvr_result_validated_at ON uaes_validation_results(validated_at);
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
    revocation_reason   TEXT,
    revoked_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_uep_plan_id ON uaes_execution_permissions(plan_id);
CREATE INDEX idx_uep_granted ON uaes_execution_permissions(granted);
CREATE INDEX idx_uep_expires_at ON uaes_execution_permissions(expires_at);
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

### 12.3 SQLAlchemy Models

All ORM models use `mapped_column` with `Mapped[]` type annotations. Models follow existing conventions:

```python
# Example: validation_result_model.py
from sqlalchemy import String, Text, Float, Integer, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ValidationResultModel(Base):
    __tablename__ = "uaes_validation_results"

    result_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("uaes_validation_requests.request_id"))
    plan_id: Mapped[str] = mapped_column(String(36), index=True)
    incident_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    decision: Mapped[str] = mapped_column(String(30), index=True)
    decision_reason: Mapped[str] = mapped_column(Text)
    summary_json: Mapped[str] = mapped_column(Text)
    rules_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    rules_passed: Mapped[int] = mapped_column(Integer, default=0)
    rules_failed: Mapped[int] = mapped_column(Integer, default=0)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    validated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    validation_duration_ms: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

---

## 13. REST API

### 13.1 Endpoint Overview

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

### 13.2 Request/Response Schemas

#### POST /api/v1/validation/validate

```python
# Request
class ValidatePlanRequest(BaseModel):
    plan_id: str
    incident_id: str | None = None
    plan_json: dict[str, Any]
    environment: str = "production"
    priority: int = 0
    timeout_seconds: int = 300
    metadata: dict[str, Any] = {}

# Response
class ValidatePlanResponse(BaseModel):
    request_id: str
    status: str  # "pending", "completed", "failed"
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
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    failures: list[ValidationFailureResponse]
    warnings: list[ValidationWarningResponse]
    approval_required: bool
    approval_level: str | None
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

### 13.3 Authentication

All endpoints use `Depends(verify_token)` dependency injection, consistent with existing API patterns.

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

## 14. Events

### 14.1 Event Overview

All events are published via `InProcessEventBus`. Events carry full context for downstream consumers.

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
| ValidationAuditLogged | Audit entry created | log_id, action, actor |
| ValidationMetricsRecorded | Metrics emitted | request_id, duration_ms, decision |

### 14.2 Event Definitions

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
```

### 14.3 Event Flow

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
   │  (self)         │ │  Engine       │ │  Engine        │
   └────────────────┘ └───────────────┘ └────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
   ValidationCompleted  Metrics Recorded    Permission Checked
   BlockerDetected      Health Updated      Execution Starts
   ApprovalRequired                         Execution Blocked
```

---

## 15. Integration

### 15.1 Planner Integration

The Validation Engine subscribes to the `PlanGenerated` event from the Planner. When a new plan is generated, the Validation Engine automatically begins validation.

```
Planner                          Validation Engine
   │                                   │
   │  PlanGenerated(event)             │
   │──────────────────────────────────▶│
   │                                   │
   │                                   │ Create ValidationRequest
   │                                   │ Run 12-stage pipeline
   │                                   │
   │  ValidationCompleted(event)       │
   │◀──────────────────────────────────│
```

**Planner publishes**: `PlanGenerated`
**Validation subscribes**: `PlanGenerated` → creates `ValidationRequest` → runs pipeline

### 15.2 Execution Engine Integration

The Execution Engine checks for an active `ExecutionPermission` before executing any plan. Without a valid permission, execution is blocked.

```
Execution Engine                   Validation Engine
      │                                   │
      │  CheckPermission(plan_id)         │
      │──────────────────────────────────▶│
      │                                   │
      │  PermissionGranted / Denied       │
      │◀──────────────────────────────────│
      │                                   │
      │  (if granted) Execute plan        │
```

### 15.3 Monitoring Integration

The Validation Engine reads health metrics and resource utilization from the Monitoring Engine to assess resource availability.

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

### 15.4 Incidents Integration

The Validation Engine reads incident severity and root cause category to assess safety and determine approval requirements.

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

### 15.5 Event Bus Integration

Full integration via `InProcessEventBus`. The Validation Engine both publishes and subscribes to events.

```python
# Event bus wiring (in setup function)
event_bus.subscribe("plan_generated", validation_service.handle_plan_generated)
event_bus.subscribe("validation_completed", execution_engine.handle_validation_completed)
event_bus.subscribe("validation_blocker_detected", notification_service.handle_blocker)
event_bus.subscribe("validation_approval_required", approval_service.handle_approval_required)
```

---

## 16. Failure Modes

### 16.1 Failure Mode Matrix

| Failure Mode | Detection | Response | Recovery |
|-------------|-----------|----------|----------|
| Validation crashes | Process restart | Revalidate on retry | Idempotent via request_id |
| Rules unavailable | Repository query fails | Default to most restrictive | Block all until rules restored |
| Database unavailable | Connection pool exhaustion | In-memory validation | Degrade persistence |
| Simulation unavailable | Timeout / connection error | Treat as "not simulated" | Warning, not blocker |
| Approval unavailable | Timeout / queue full | Queue for later | Timeout escalation |
| External dependency unavailable | Connection error | Log, skip non-critical | Retry with backoff |

### 16.2 Graceful Degradation

**Validation crashes**: The pipeline is idempotent via `request_id`. If the engine crashes mid-validation, the request can be retried and the pipeline will re-run from the beginning. No partial state is persisted.

**Rules unavailable**: If the rule repository is unavailable, the system defaults to the **most restrictive** mode: all rules are treated as BLOCKER and all plans are rejected. This is a safe failure mode — it is better to reject a valid plan than to approve a dangerous one.

**Database unavailable**: If the database is unavailable, the engine can still perform validation in-memory. Results are not persisted, but the validation decision is still returned to the caller. The audit log is queued for later persistence.

**Simulation unavailable**: If the simulation service is unavailable, the simulation assessment is marked as "not_performed". This generates a WARNING (not a BLOCKER) unless the plan has high risk, in which case it becomes a BLOCKER.

**Approval unavailable**: If the approval system is unavailable, the validation result is stored with `PENDING_APPROVAL` status. When the approval system becomes available, pending approvals are processed. Timeout escalation still applies.

**External dependency unavailable**: Non-critical external dependencies (e.g., cost estimation service) are skipped with a warning. Critical dependencies (e.g., auth service) cause the pipeline to fail.

### 16.3 Idempotency

Every validation request carries a unique `request_id`. The pipeline is designed to be idempotent:

- If a request with the same `request_id` is submitted twice, the second submission returns the existing result
- Rule evaluations are deterministic given the same input
- Approval decisions are idempotent — approving an already-approved request returns the existing approval

---

## 17. Security

### 17.1 Authentication

All API endpoints use JWT-based authentication via `Depends(verify_token)`, consistent with the existing auth pattern.

```python
@router.post("/validate")
async def validate_plan(
    request: ValidatePlanRequest,
    token: dict = Depends(verify_token),
) -> ValidatePlanResponse:
    # token contains: sub (user_id), roles, exp
    ...
```

### 17.2 Authorization

Role-based access control (RBAC) with 5 roles:

| Role | Permissions |
|------|------------|
| `developer` | Submit validation, view results, view rules/policies |
| `maintainer` | + Approve/reject plans, view pending approvals |
| `operations` | + Manage rules/policies, emergency override |
| `administrator` | + Revoke permissions, manage audit logs |
| `emergency` | + Emergency override with full audit |

### 17.3 Audit Logging

Every decision is logged with:
- **Actor**: Who made the decision (user ID or "system")
- **Timestamp**: When the decision was made
- **IP Address**: Client IP address
- **Details**: Full decision context (JSON)
- **Action**: What action was taken (validate, approve, reject, revoke)

```python
audit_entry = AuditLogEntry(
    log_id=str(uuid.uuid4()),
    result_id=result.result_id,
    plan_id=request.plan_id,
    action="validation_completed",
    actor=token["sub"],
    details_json=json.dumps({
        "decision": decision.decision,
        "risk_score": safety.risk_score.value,
        "rules_evaluated": len(failures) + len(warnings),
    }),
    ip_address=request.client.host,
    timestamp=datetime.utcnow(),
)
```

### 17.4 Tamper Protection

The audit log is designed for tamper-evidence:

- Each log entry includes a `log_id` and `timestamp`
- Log entries are append-only (no updates, no deletes)
- Future enhancement: hash-chain integrity (each entry includes hash of previous entry)
- The audit log is stored in a separate table with restricted write access

### 17.5 Approval Recording

The full approval chain is recorded:

```
ApprovalDecision #1: PENDING (system)
ApprovalDecision #2: APPROVED by user_123 at 14:30 with conditions
ExecutionPermission #1: GRANTED by system at 14:30, expires at 18:30
AuditLog #1: validation.approval_granted at 14:30 by user_123
```

Every approval includes:
- Who approved/rejected
- When they approved/rejected
- What conditions they attached
- What their approval level was
- When the approval expires

---

## 18. Performance

### 18.1 Latency Targets

| Scenario | Target Latency | Measurement |
|----------|---------------|-------------|
| Auto-approved (dev/staging) | < 500ms | End-to-end pipeline |
| Approval-required | < 2s | Pipeline + approval check |
| Complex validation (>20 rules) | < 5s | Pipeline with many rules |
| Database round-trip | < 50ms | Repository operations |

### 18.2 Caching Strategy

**Rules and policies** are cached in-memory with a 5-minute TTL. Cache is invalidated on:
- Rule/policy update via API
- Cache TTL expiry
- Application restart

```python
class RulePolicyCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self._rules: dict[str, ValidationRule] = {}
        self._policies: dict[str, ValidationPolicy] = {}
        self._last_refresh: datetime = datetime.min
        self._ttl = timedelta(seconds=ttl_seconds)

    async def get_rules(self, rule_repository: RuleRepository) -> list[ValidationRule]:
        if datetime.utcnow() - self._last_refresh > self._ttl:
            await self._refresh(rule_repository)
        return list(self._rules.values())
```

### 18.3 Scalability

- **Horizontal scaling**: The Validation Engine is stateless. Multiple instances can run behind a load balancer.
- **Validation workers**: Separate validation workers can process pipeline stages in parallel.
- **Database**: Connection pooling via SQLAlchemy's async pool. Read replicas for query-heavy operations.

### 18.4 Concurrency

All service methods are `async`. No blocking I/O operations. The pipeline stages are sequential by design (each stage depends on previous outputs), but independent analyzers can run concurrently within a stage.

```python
# Concurrent assessments within a stage
async def _run_assessments(self, request: ValidationRequest) -> dict[str, Any]:
    safety, dependency, compatibility, rollback, simulation, resource, security = await asyncio.gather(
        self._safety_assessor.assess(request),
        self._dependency_analyzer.analyze(request),
        self._compatibility_analyzer.analyze(request),
        self._rollback_analyzer.analyze(request),
        self._simulation_verifier.verify(request),
        self._resource_analyzer.analyze(request),
        self._security_analyzer.analyze(request),
    )
    return {
        "safety": safety,
        "dependency": dependency,
        "compatibility": compatibility,
        "rollback": rollback,
        "simulation": simulation,
        "resource": resource,
        "security": security,
    }
```

### 18.5 Throughput

- **Target**: 100 validations/second sustained
- **Burst**: 500 validations/second for 10 seconds
- **Bottleneck**: Database writes (audit log, results). Mitigated by batch inserts and connection pooling.

---

## 19. Testing Strategy

### 19.1 Unit Tests

- **100% rule coverage**: Every validation rule (30+) has at least one test
- **All domain models**: Every model is tested for construction, validation, serialization
- **All value objects**: Range validation, property methods, edge cases
- **All enums**: Verify string values, membership, serialization
- **Service unit tests**: Mocked repositories, verify logic in isolation

### 19.2 Integration Tests

- **Full pipeline**: End-to-end validation with real repository implementations
- **Repository round-trips**: Save and retrieve each model type
- **Event dispatch**: Verify events are published on correct triggers
- **API endpoint tests**: Full HTTP request/response cycle
- **Database migrations**: Verify migration up/down works correctly

### 19.3 Stress Tests

- **Concurrent validations**: 100 simultaneous validation requests
- **Timeout handling**: Validation timeout triggers correctly
- **Connection pool exhaustion**: Graceful degradation under DB pressure
- **Memory pressure**: Large number of cached rules/policies

### 19.4 Chaos Tests

- **Database failure**: In-memory validation works correctly
- **Rule engine failure**: Default to restrictive mode
- **Approval timeout**: Escalation triggers correctly
- **Partial validation**: Pipeline halts on blocker, produces correct partial result

### 19.5 Failure Simulation

- **Rule engine crash recovery**: Pipeline recovers and produces valid result
- **Partial validation**: Some analyzers succeed, others fail — decision still made
- **Approval system down**: Queued for later, timeout escalation still works

### 19.6 Test File Map

```
tests/unit/
├── test_validation_request.py          # Request construction, validation
├── test_validation_result.py           # Result construction, serialization
├── test_validation_decision.py         # Decision logic, conditions
├── test_validation_rule.py             # Rule construction, conditions
├── test_validation_policy.py           # Policy construction, enforcement
├── test_validation_evidence.py         # Evidence construction, confidence
├── test_validation_failure.py          # Failure construction, severity
├── test_validation_warning.py          # Warning construction, message
├── test_approval_decision.py           # Approval construction, expiry
├── test_execution_permission.py        # Permission grant/revoke
├── test_execution_blocker.py           # Blocker construction, resolution
├── test_safety_assessment.py           # Safety assessment logic
├── test_compatibility_assessment.py    # Compatibility checks
├── test_rollback_assessment.py         # Rollback feasibility
├── test_simulation_assessment.py       # Simulation verification
├── test_dependency_assessment.py       # Dependency analysis
├── test_resource_assessment.py         # Resource checks
├── test_security_assessment.py         # Security checks
├── test_cost_assessment.py             # Cost estimation
├── test_confidence_score.py            # ConfidenceScore validation
├── test_risk_score.py                  # RiskScore validation
├── test_time_range.py                  # TimeRange validation
├── test_threshold_range.py             # ThresholdRange validation
├── test_component_descriptor.py        # ComponentDescriptor
├── test_environment_descriptor.py      # EnvironmentDescriptor
├── test_version_constraint.py          # VersionConstraint
├── test_resource_quota.py              # ResourceQuota
├── test_maintenance_window.py          # MaintenanceWindow
├── test_rule_engine.py                 # Rule evaluation
├── test_policy_engine.py               # Policy evaluation
├── test_approval_engine.py             # Approval workflow
├── test_decision_engine.py             # Decision aggregation
└── test_summary_generator.py           # Summary generation

tests/integration/
├── test_validation_pipeline.py         # Full pipeline flow
├── test_validation_repository.py       # Repository CRUD
├── test_rule_repository.py             # Rule repository
├── test_policy_repository.py           # Policy repository
├── test_evidence_repository.py         # Evidence repository
├── test_audit_repository.py            # Audit repository
├── test_event_dispatch.py              # Event publishing
└── test_full_validation_flow.py        # End-to-end validation

tests/stress/
├── test_concurrent_validations.py      # 100 concurrent requests
└── test_timeout_handling.py            # Timeout scenarios

tests/chaos/
├── test_database_failure.py            # DB unavailable
├── test_rule_engine_failure.py         # Rules unavailable
├── test_approval_timeout.py            # Approval system down
└── test_partial_validation.py          # Partial pipeline completion
```

---

## 20. Definition of Done

### 20.1 Domain Layer

- [ ] All 18 domain models implemented with `frozen=True` and `use_enum_values=True`
- [ ] All 9 value objects implemented with validation
- [ ] All 12+ enums implemented as `StrEnum`
- [ ] Domain events defined and typed
- [ ] Domain layer has zero external dependencies

### 20.2 Application Layer

- [ ] All 13 services implemented
- [ ] All repository port interfaces defined as `Protocol`
- [ ] Event publisher port interface defined
- [ ] 12-stage validation pipeline complete
- [ ] Pipeline is idempotent via `request_id`

### 20.3 Infrastructure Layer

- [ ] All 7 database tables with SQLAlchemy ORM models
- [ ] Alembic migration created and tested (up/down)
- [ ] All 5 repository implementations with async SQLAlchemy
- [ ] In-process event publisher implemented
- [ ] Rule/policy cache with 5-minute TTL

### 20.4 API Layer

- [ ] All 10 REST endpoints implemented
- [ ] All request/response schemas defined
- [ ] `Depends(verify_token)` auth on all endpoints
- [ ] OpenAPI documentation generated

### 20.5 Rules & Policies

- [ ] All 8 Safety rules (SAFETY_001-008) implemented
- [ ] All 5 Dependency rules (DEPENDENCY_001-005) implemented
- [ ] All 5 Compatibility rules (COMPAT_001-005) implemented
- [ ] All 5 Resource rules (RESOURCE_001-005) implemented
- [ ] All 8 Policy rules (POLICY_001-008) implemented
- [ ] All 4 Security rules (SECURITY_001-004) implemented
- [ ] All 4 Rollback rules (ROLLBACK_001-004) implemented
- [ ] Total: 39 rules implemented and tested

### 20.6 Approval System

- [ ] 5-level approval hierarchy working
- [ ] Escalation matrix implemented
- [ ] Timeout rules (24h, 4h, 1h, 30m) implemented
- [ ] Delegation rules implemented
- [ ] Conditional approval with condition checking

### 20.7 Events

- [ ] All 16 domain events defined and typed
- [ ] Events published on correct triggers
- [ ] Events consumed by downstream systems

### 20.8 Testing

- [ ] 692+ existing tests pass (no regressions)
- [ ] New validation tests: 150+ tests
- [ ] Unit test coverage: 100% for rules, models, value objects
- [ ] Integration tests: Full pipeline, repositories, events
- [ ] Stress tests: Concurrent validations, timeouts
- [ ] Chaos tests: Database failures, rule failures, approval timeouts

### 20.9 Code Quality

- [ ] `ruff check` clean (zero errors)
- [ ] `ruff format` clean (zero changes)
- [ ] No circular dependencies
- [ ] No domain layer leaks (validation doesn't import planner/executor internals)
- [ ] All type annotations correct (mypy strict pass)

### 20.10 Documentation

- [ ] This architecture document complete and frozen
- [ ] API documentation auto-generated from OpenAPI
- [ ] Rule catalog documented with conditions and severity
- [ ] Approval policy documented with escalation matrix

---

## Appendix A: Dependency Graph

```
                    ┌─────────────────┐
                    │   Domain Layer   │
                    │  (no deps)       │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Application Layer│
                    │  (ports, svcs)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼───────┐ ┌───▼────┐ ┌──────▼──────┐
     │  Infrastructure │ │  API   │ │  Tests      │
     │  (repos, cache) │ │(routes)│ │  (unit/int) │
     └────────────────┘ └────────┘ └─────────────┘
```

## Appendix B: Data Flow

```
Planner                    Validation Engine                   Execution Engine
   │                              │                                  │
   │  PlanGenerated               │                                  │
   │─────────────────────────────▶│                                  │
   │                              │                                  │
   │                              │  ┌─────────────────────┐        │
   │                              │  │ 12-Stage Pipeline   │        │
   │                              │  │                     │        │
   │                              │  │ Stages 1-9:         │        │
   │                              │  │   Assessments       │        │
   │                              │  │                     │        │
   │                              │  │ Stage 10:           │        │
   │                              │  │   Rules → Blockers  │        │
   │                              │  │                     │        │
   │                              │  │ Stage 11:           │        │
   │                              │  │   Policies → Blockers│       │
   │                              │  │                     │        │
   │                              │  │ Stage 12:           │        │
   │                              │  │   Decision          │        │
   │                              │  └─────────┬───────────┘        │
   │                              │            │                    │
   │                              │  ┌─────────▼───────────┐        │
   │                              │  │ Persist Results     │        │
   │                              │  │ Emit Events         │        │
   │                              │  │ Grant Permission    │        │
   │                              │  └─────────────────────┘        │
   │                              │            │                    │
   │  ValidationCompleted         │            │                    │
   │◀─────────────────────────────│            │                    │
   │                              │            │                    │
   │                              │  ValidationPermissionGranted    │
   │                              │────────────────────────────────▶│
   │                              │            │                    │
   │                              │            │  Check Permission  │
   │                              │            │  Execute Plan      │
   │                              │            │                    │
```

## Appendix C: Enum Reference

| Enum | Values | Count |
|------|--------|-------|
| ValidationStatus | pending, in_progress, completed, failed, timed_out | 5 |
| ValidationDecisionEnum | approved, rejected, conditional, pending_approval, expired | 5 |
| ValidationSeverity | blocker, warning, info | 3 |
| ValidationCategory | safety, dependency, compatibility, resource, policy, security, rollback, cost | 8 |
| ApprovalLevel | auto, developer, maintainer, operations, administrator, emergency | 6 |
| ApprovalStatus | pending, approved, rejected, escalated, expired | 5 |
| ExecutionPermissionStatus | granted, denied, expired, revoked | 4 |
| CascadeRisk | low, medium, high, critical | 4 |
| RollbackComplexity | low, medium, high, impossible | 4 |
| PolicyEnforcement | hard, soft | 2 |
| PolicyType | approval, cost, maintenance, production, security, business | 6 |
| BlockerType | rule_violation, policy_violation, approval_required, safety, resource, security | 6 |

**Total enum values: 58**

## Appendix D: Checklist Summary

| Category | Item | Count |
|----------|------|-------|
| Domain Models | validation_request, validation_result, validation_decision, validation_rule, validation_policy, validation_evidence, validation_failure, validation_warning, approval_decision, execution_permission, execution_blocker, safety_assessment, compatibility_assessment, rollback_assessment, simulation_assessment, dependency_assessment, resource_assessment, security_assessment, cost_assessment | 19 |
| Value Objects | confidence_score, risk_score, time_range, threshold_range, component_descriptor, environment_descriptor, version_constraint, resource_quota, maintenance_window | 9 |
| Enums | 12 enum types, 58 total values | 12 |
| Services | validation_service, rule_engine, policy_engine, approval_engine, dependency_analyzer, compatibility_analyzer, rollback_analyzer, security_analyzer, simulation_verifier, environment_analyzer, resource_analyzer, decision_engine, summary_generator | 13 |
| Rules | SAFETY_001-008, DEPENDENCY_001-005, COMPAT_001-005, RESOURCE_001-005, POLICY_001-008, SECURITY_001-004, ROLLBACK_001-004 | 39 |
| Database Tables | validation_requests, validation_results, validation_failures, validation_warnings, validation_evidence, approval_decisions, execution_permissions, audit_log | 8 |
| API Endpoints | validate, get_result, get_by_plan, pending_approvals, approve, reject, check_permission, revoke_permission, list_rules, list_policies | 10 |
| Events | requested, started, completed, failed, rule_triggered, blocker_detected, warning_generated, approval_required, approval_granted, approval_rejected, approval_escalated, permission_granted, permission_revoked, expired, audit_logged, metrics_recorded | 16 |
| Tests | 150+ new tests across unit/integration/stress/chaos | 150+ |

---

> **END OF DOCUMENT**
>
> This document is frozen for implementation. Any changes require a formal architecture review.
