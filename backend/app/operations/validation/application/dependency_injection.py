"""
Dependency Injection for the Validation Engine application layer.

This module defines the registration contract through which the
application layer exposes its composition root.

No concrete implementations, no container, no runtime wiring —
only protocol-based contracts.

Usage (in Milestone 2B+):

    from app.operations.validation.application.dependency_injection import (
        ValidationModule,
    )

    # The future DI container owns object creation.
    # ValidationModule merely describes what registrations exist.
    module: ValidationModule = ...  # resolved by framework
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.operations.validation.application.ports.approval_provider import (
        ApprovalProvider,
    )
    from app.operations.validation.application.ports.audit_logger import (
        AuditLogger,
    )
    from app.operations.validation.application.ports.cache_provider import (
        CacheProvider,
    )
    from app.operations.validation.application.ports.policy_repository import (
        PolicyRepository,
    )
    from app.operations.validation.application.ports.rule_repository import (
        RuleRepository,
    )
    from app.operations.validation.application.ports.signature_provider import (
        SignatureProvider,
    )
    from app.operations.validation.application.ports.validation_history_repository import (
        ValidationHistoryRepository,
    )


@runtime_checkable
class ValidationModule(Protocol):
    """
    Registration contract for the Validation Engine bounded context.

    This protocol describes *what* can be registered, not *how*
    objects are created.  A future DI container owns instantiation;
    this contract only exposes registration slots for each port
    that the ValidationService depends on.
    """

    def register_approval_provider(self, provider: ApprovalProvider) -> None:
        """Register an ApprovalProvider adapter."""
        ...

    def register_policy_repository(self, repository: PolicyRepository) -> None:
        """Register a PolicyRepository adapter."""
        ...

    def register_rule_repository(self, repository: RuleRepository) -> None:
        """Register a RuleRepository adapter."""
        ...

    def register_cache_provider(self, provider: CacheProvider) -> None:
        """Register a CacheProvider adapter."""
        ...

    def register_audit_logger(self, logger: AuditLogger) -> None:
        """Register an AuditLogger adapter."""
        ...

    def register_signature_provider(self, provider: SignatureProvider) -> None:
        """Register a SignatureProvider adapter."""
        ...

    def register_history_repository(self, repository: ValidationHistoryRepository) -> None:
        """Register a ValidationHistoryRepository adapter."""
        ...
