import Foundation

/// Generic orchestrator for a category of `ServiceProvider` implementations.
///
/// `ServiceOrchestrator` manages provider registration, selection by
/// capability and priority, retry with backoff, automatic failover
/// across providers, and circuit breaker protection.
///
/// ## Type Parameters
///
/// - `P`: The provider type. Must conform to `ServiceProvider`.
///
/// ## Thread Safety
///
/// Confined to `@MainActor` for compatibility with DI and lifecycle.
/// Circuit breakers are independent actors.
@MainActor
public final class ServiceOrchestrator<P: ServiceProvider> {

    // MARK: - Types

    /// Internal runtime state for a registered provider.
    private struct Entry {
        let provider: P
        let config: ProviderConfig
        var metrics: ProviderMetrics
        let breaker: CircuitBreaker
    }

    // MARK: - Properties

    public let config: OrchestratorConfig
    public let logger: Logger

    private let retryEngine = RetryEngine()
    private var entries: [Entry] = []
    private var initialized = false

    // MARK: - Initialization

    public init(config: OrchestratorConfig, logger: Logger) {
        self.config = config
        self.logger = logger
    }

    // MARK: - Registration

    /// Registers a provider with the orchestrator.
    ///
    /// Providers are sorted by their configured priority after registration.
    public func register(_ provider: P, configuration: ProviderConfig) {
        let threshold = configuration.failureThreshold ?? config.defaultFailureThreshold
        let breaker = CircuitBreaker(
            failureThreshold: threshold,
            cooldownDuration: config.cooldownDuration
        )
        let entry = Entry(
            provider: provider,
            config: configuration,
            metrics: ProviderMetrics(),
            breaker: breaker
        )
        entries.removeAll { $0.provider.providerID == provider.providerID }
        entries.append(entry)
        entries.sort { $0.config.priority < $1.config.priority }
    }

    /// Returns the list of registered provider IDs in priority order.
    public func registeredProviderIDs() -> [String] {
        entries.map(\.provider.providerID)
    }

    // MARK: - Execution

    /// Executes a request, automatically selecting a provider, retrying,
    /// and failing over to alternatives as needed.
    public func execute(
        request: any Sendable,
        capability: ServiceCapability? = nil
    ) async throws -> any Sendable {
        guard config.enabled else {
            throw OrchestrationError.allProvidersExhausted(category: config.category, attempted: [])
        }

        var attempted: [String] = []

        for entry in entries {
            guard entry.config.enabled else { continue }
            if let capability, !entry.config.capabilities.contains(capability) { continue }

            attempted.append(entry.provider.providerID)

            guard await entry.breaker.allowRequest() else { continue }

            let policy = entry.config.retryPolicy ?? config.defaultRetryPolicy
            let providerID = entry.provider.providerID

            do {
                let result = try await retryEngine.execute(with: policy) { [self] in
                    try await executeWithProvider(entry, request: request)
                }
                return result
            } catch {
                await logger.warning("Provider failed, failing over", metadata: [
                    "provider": providerID,
                ])
            }
        }

        throw OrchestrationError.allProvidersExhausted(category: config.category, attempted: attempted)
    }

    /// Executes a request against a specific provider entry.
    private func executeWithProvider(
        _ entry: Entry,
        request: any Sendable
    ) async throws -> any Sendable {
        var mutableEntry = entry
        let start = Date()

        do {
            let result = try await entry.provider.execute(request: request)
            let latency = Date().timeIntervalSince(start)
            mutableEntry.metrics.recordSuccess(latency: latency)
            await mutableEntry.breaker.recordSuccess()
            if let idx = entries.firstIndex(where: { $0.provider.providerID == entry.provider.providerID }) {
                entries[idx] = mutableEntry
            }
            return result
        } catch {
            mutableEntry.metrics.recordFailure(error: String(describing: error))
            await mutableEntry.breaker.recordFailure()
            if let idx = entries.firstIndex(where: { $0.provider.providerID == entry.provider.providerID }) {
                entries[idx] = mutableEntry
            }
            throw error
        }
    }

    // MARK: - Health

    /// Returns the current health status of all registered providers.
    public func providerHealth() -> [(providerID: String, status: HealthStatus, metrics: ProviderMetrics)] {
        entries.map { entry in
            let status: HealthStatus
            if !entry.config.enabled {
                status = .unhealthy
            } else if entry.metrics.consecutiveFailures >= (entry.config.failureThreshold ?? config.defaultFailureThreshold) {
                status = entry.metrics.isCooldownExpired ? .degraded : .inCooldown
            } else if entry.metrics.consecutiveFailures > 0 {
                status = .degraded
            } else {
                status = .healthy
            }
            return (entry.provider.providerID, status, entry.metrics)
        }
    }

    /// Resets all circuit breakers and metrics.
    public func resetAll() async {
        for entry in entries {
            await entry.breaker.reset()
        }
        for i in entries.indices {
            entries[i].metrics.reset()
        }
    }

    // MARK: - Lifecycle

    /// Initializes all registered providers.
    public func initializeAll() async throws {
        guard !initialized else { return }
        for entry in entries {
            try await entry.provider.initialize()
        }
        initialized = true
        await logger.info("Orchestrator initialized", metadata: [
            "category": config.category.rawValue,
            "providers": "\(entries.count)",
        ])
    }

    /// Shuts down all registered providers.
    public func shutdownAll() async {
        for entry in entries {
            await entry.provider.shutdown()
        }
    }
}
