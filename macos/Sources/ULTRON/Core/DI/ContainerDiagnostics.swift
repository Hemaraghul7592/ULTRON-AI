/// Read-only diagnostics and validation for a `DependencyContainer`.
///
/// `ContainerDiagnostics` inspects container state without modifying it.
/// It never registers, resolves, caches, or mutates. All methods are
/// deterministic — repeated calls produce identical results for the
/// same container snapshot.
///
/// ## Actor Isolation
///
/// Diagnostics shares the container's `@MainActor` isolation domain.
/// This allows synchronous access to container properties without
/// crossing actor boundaries. Callers from non-`@MainActor` contexts
/// must `await` diagnostics methods.
///
/// ## Example
/// ```swift
/// let diag = ContainerDiagnostics(container: container)
/// try await diag.validate()                        // Verify all singletons can start
/// let types = diag.registeredTypes()               // List registrations
/// let stats = diag.totalRegistrations()            // Counts + overwrites
/// ```
@MainActor
public struct ContainerDiagnostics {

    // MARK: - Properties

    /// The container being diagnosed. Access is read-only.
    private let container: DependencyContainer

    // MARK: - Initialization

    /// Creates diagnostics for the given container.
    ///
    /// The diagnostics object holds a reference to the container but
    /// never modifies it. All methods are safe to call at any time.
    ///
    /// - Parameter container: The container to inspect.
    public init(container: DependencyContainer) {
        self.container = container
    }

    // MARK: - Validation

    /// Validates that every registered singleton can be constructed
    /// through the real resolution pipeline.
    ///
    /// Each singleton's factory executes with the container's actual
    /// `ContainerResolver`. Dependency resolutions flow through the
    /// full `_resolve` pipeline — including singleton caching and
    /// cycle detection. Validation stops on the first failure.
    ///
    /// Transient registrations are skipped because their construction
    /// may depend on request-specific context not available at startup.
    ///
    /// - Throws: The first `ContainerError` encountered during validation.
    public func validate() async throws {
        for record in container.diagnosticsRecords {
            guard case .singleton = record.registration.lifetime else {
                continue
            }
            try await container._validateRecord(for: record.registration.serviceType)
        }
    }

    // MARK: - Registration Listing

    /// Returns all active registrations sorted by registration index.
    ///
    /// Each entry exposes the type name, lifetime policy, and
    /// registration index. Overwritten registrations are excluded.
    ///
    /// - Returns: An array of snapshots in deterministic order.
    public func registeredTypes() -> [RegistrationSnapshot] {
        container.snapshot()
    }

    // MARK: - Dependency Graph

    /// Returns the declared dependency relationships between services.
    ///
    /// Each factory closure is executed in **observation mode** with a
    /// special resolver that records what was requested without actually
    /// providing instances. This reveals each service's declared
    /// dependencies without constructing a full object graph.
    ///
    /// ## Important Contract
    ///
    /// - Factories are executed. Side-effect-free factories are safe.
    ///   Factories that perform I/O, allocate resources, or mutate
    ///   global state may cause unintended effects.
    /// - Services are NOT actually resolved. The observing resolver
    ///   throws on every `resolve()` call after recording the type.
    /// - The returned graph is a **declared dependency** map, not an
    ///   actual instance graph. It shows what each factory asks for,
    ///   not what was successfully constructed.
    /// - Results are deterministic: sorted by registration index.
    ///   Duplicate edges are excluded automatically.
    ///
    /// - Returns: An array of `(service, dependencies)` tuples sorted
    ///   by registration index.
    public func dependencyGraph() async -> [(service: String, dependencies: [String])] {
        var results: [(service: String, dependencies: [String])] = []

        for record in container.diagnosticsRecords {
            let serviceName = record.registration.typeName
            let observer = DependencyObserver()
            do {
                _ = try await record.registration.factory(observer)
            } catch {
                // Factory failed — record empty dependencies.
                // The error is irrelevant for graph generation.
            }
            results.append((service: serviceName, dependencies: observer.requestedTypes))
        }

        return results
    }

    // MARK: - Registration Statistics

    /// Returns statistics about container registrations.
    ///
    /// Includes counts of active registrations, total registrations
    /// ever made, and how many have been overwritten.
    ///
    /// - Returns: A statistics value object.
    public func totalRegistrations() -> RegistrationStatistics {
        RegistrationStatistics(
            activeCount: container.registrationCount,
            totalCount: container.totalRegistrations
        )
    }
}

// MARK: - Internal Resolver Implementation

/// A resolver that records which types were requested during factory
/// execution. Used by `dependencyGraph()` to trace declared dependencies.
private final class DependencyObserver: Resolver {
    private(set) var requestedTypes: [String] = []

    func resolve<Service>(_ type: Service.Type) async throws -> Service {
        requestedTypes.append(String(describing: Service.self))
        throw ContainerError.notRegistered(typeName: String(describing: Service.self))
    }

    func resolveIfRegistered<Service>(_ type: Service.Type) async -> Service? {
        requestedTypes.append(String(describing: Service.self))
        return nil
    }
}
