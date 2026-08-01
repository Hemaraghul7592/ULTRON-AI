import Foundation

/// Configuration for a `ServiceOrchestrator` instance.
///
/// Specifies global defaults for retry, circuit breaker behavior,
/// and enabled/disabled state. Individual providers can override
/// these defaults via `ProviderConfig`.
public struct OrchestratorConfig: Sendable {

    /// The category this orchestrator manages.
    public let category: ServiceCategory

    /// Default retry policy used when a provider does not specify its own.
    public let defaultRetryPolicy: RetryPolicy

    /// Default consecutive failures before a provider's breaker opens.
    public let defaultFailureThreshold: Int

    /// Default cooldown duration in seconds.
    public let cooldownDuration: TimeInterval

    /// Whether this orchestrator is enabled. When false, all requests
    /// fail immediately.
    public let enabled: Bool

    public init(
        category: ServiceCategory,
        defaultRetryPolicy: RetryPolicy = .standard,
        defaultFailureThreshold: Int = 5,
        cooldownDuration: TimeInterval = 600,
        enabled: Bool = true
    ) {
        self.category = category
        self.defaultRetryPolicy = defaultRetryPolicy
        self.defaultFailureThreshold = defaultFailureThreshold
        self.cooldownDuration = cooldownDuration
        self.enabled = enabled
    }
}
