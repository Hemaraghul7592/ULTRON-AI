/// Internal concrete implementation of the `Resolver` protocol.
///
/// `ContainerResolver` is a thin wrapper that delegates resolution
/// requests to the `DependencyContainer`. Factory closures receive
/// a `ContainerResolver` instance — they never see the full container
/// API, preventing the service locator anti-pattern.
@MainActor
final class ContainerResolver: Resolver {

    // MARK: - Properties

    /// The container that handles actual resolution.
    /// Unowned to avoid a retain cycle: the container owns its
    /// registration records, and ContainerResolver is created
    /// on-the-fly during resolution.
    private unowned let container: DependencyContainer

    // MARK: - Initialization

    /// Creates a resolver that delegates to the given container.
    ///
    /// - Parameter container: The container that performs resolution.
    init(container: DependencyContainer) {
        self.container = container
    }

    // MARK: - Resolver

    func resolve<Service: Sendable>(_ type: Service.Type) async throws -> Service {
        try await container._resolve(type)
    }

    func resolveIfRegistered<Service: Sendable>(_ type: Service.Type) async -> Service? {
        await container._resolveIfRegistered(type)
    }
}
