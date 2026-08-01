/// A `LifecycleHook` that validates all providers in an orchestrator
/// during the application startup phase.
///
/// Registered during the `.dependencyInjection` startup phase (priority 50).
/// If any provider fails its health check, the hook logs a warning but
/// does not prevent the application from launching.
@MainActor
public struct OrchestrationLifecycleHook<P: ServiceProvider>: LifecycleHook {

    public let phase: StartupPhase = .dependencyInjection
    public let priority: Int = 50
    public let label: String

    private let orchestrator: ServiceOrchestrator<P>
    private let logger: Logger

    public init(orchestrator: ServiceOrchestrator<P>, logger: Logger) {
        self.orchestrator = orchestrator
        self.logger = logger
        label = "Orchestration-\(orchestrator.config.category.rawValue)"
    }

    public func onStartup() async throws {
        try await orchestrator.initializeAll()
        let health = orchestrator.providerHealth()
        let healthy = health.filter { $0.status == .healthy }

        if healthy.count == health.count {
            await logger.info("All providers healthy", metadata: [
                "category": orchestrator.config.category.rawValue,
                "count": "\(healthy.count)",
            ])
        } else {
            await logger.warning("Some providers unhealthy", metadata: [
                "category": orchestrator.config.category.rawValue,
                "healthy": "\(healthy.count)",
                "total": "\(health.count)",
            ])
        }
    }

    public func onShutdown() async {
        await orchestrator.shutdownAll()
    }
}
