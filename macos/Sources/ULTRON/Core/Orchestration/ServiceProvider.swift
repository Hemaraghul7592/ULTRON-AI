/// Universal protocol for all external service integrations.
///
/// Every provider — regardless of category — conforms to this ONE
/// protocol. The orchestrator works with `any ServiceProvider` and
/// never contains provider-specific logic.
///
/// ## Concurrency
///
/// Conforming types must be `Sendable`. Providers that need mutable
/// state should use actors or `@MainActor` classes.
public protocol ServiceProvider: Identifiable, Sendable {

    /// A unique identifier for this provider instance.
    var providerID: String { get }

    /// A human-readable name for diagnostics and logging.
    var providerName: String { get }

    /// The category this provider belongs to.
    var category: ServiceCategory { get }

    /// The capabilities this provider supports.
    var capabilities: Set<ServiceCapability> { get }

    /// Initialize provider resources. Called once during startup.
    func initialize() async throws

    /// Perform a health check. Returns current status.
    func healthCheck() async -> HealthStatus

    /// Execute a request against this provider.
    ///
    /// The request is any `Sendable` value. The provider is responsible
    /// for decoding it into the expected type.
    ///
    /// - Parameter request: An opaque request payload.
    /// - Returns: An opaque result payload.
    /// - Throws: Provider-specific errors, which the orchestrator
    ///   normalizes into `OrchestrationError`.
    func execute(request: any Sendable) async throws -> any Sendable

    /// Release provider resources. Called during shutdown.
    func shutdown() async

    /// Reset internal state after recovery. Called when a provider
    /// transitions from unhealthy back to healthy.
    func reset() async
}

// MARK: - Default Implementations

public extension ServiceProvider {
    var id: String { providerID }

    func reset() async {}
    func shutdown() async {}
}
