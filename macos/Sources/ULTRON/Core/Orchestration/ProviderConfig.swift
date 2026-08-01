/// Configuration for a single provider within an orchestrator.
///
/// Provider priority determines selection order: lower values are
/// tried first. The orchestrator selects the lowest-priority healthy
/// provider that supports the requested capability.
public struct ProviderConfig: Sendable {

    /// Unique identifier matching `ServiceProvider.providerID`.
    public let providerID: String

    /// Selection priority. Lower = tried first.
    public let priority: Int

    /// The capabilities this provider supports.
    public let capabilities: Set<ServiceCapability>

    /// Optional per-provider retry override. Falls back to the
    /// orchestrator's default retry policy when nil.
    public let retryPolicy: RetryPolicy?

    /// Optional per-provider circuit breaker threshold override.
    public let failureThreshold: Int?

    /// Whether this provider is enabled. Disabled providers are
    /// fully skipped during selection.
    public let enabled: Bool

    public init(
        providerID: String,
        priority: Int = 0,
        capabilities: Set<ServiceCapability> = [],
        retryPolicy: RetryPolicy? = nil,
        failureThreshold: Int? = nil,
        enabled: Bool = true
    ) {
        self.providerID = providerID
        self.priority = priority
        self.capabilities = capabilities
        self.retryPolicy = retryPolicy
        self.failureThreshold = failureThreshold
        self.enabled = enabled
    }
}
