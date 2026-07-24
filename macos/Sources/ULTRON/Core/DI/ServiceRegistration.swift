/// Immutable configuration captured at registration time.
///
/// `ServiceRegistration` records the caller's intent — what type to
/// register, how long it should live, and how to construct it. It is
/// created once during `register()` and never modified afterward.
///
/// The container wraps each `ServiceRegistration` in a `ServiceRecord`
/// to add runtime state (singleton cache, registration index).
public struct ServiceRegistration {

    // MARK: - Properties

    /// The type being registered, stored as an `ObjectIdentifier` for
    /// type-safe lookup without string-based identifiers.
    public let serviceType: ObjectIdentifier

    /// A human-readable name for the registered type, derived from
    /// the Swift metatype at registration time (e.g., `"Database"`).
    /// Used by diagnostics and logging — never for lookup.
    public let typeName: String

    /// The lifetime policy chosen at registration time.
    public let lifetime: ServiceLifetime

    /// The factory closure that constructs an instance of the service.
    /// Receives a `Resolver` so the service can resolve its own
    /// dependencies during construction.
    public let factory: (any Resolver) async throws -> Any

    // MARK: - Initialization

    /// Creates a new registration configuration.
    ///
    /// - Parameters:
    ///   - serviceType: The type being registered.
    ///   - typeName: A human-readable name for diagnostics.
    ///   - lifetime: How long the service should live.
    ///   - factory: A closure that constructs the service.
    public init(
        serviceType: ObjectIdentifier,
        typeName: String,
        lifetime: ServiceLifetime,
        factory: @escaping (any Resolver) async throws -> Any
    ) {
        self.serviceType = serviceType
        self.typeName = typeName
        self.lifetime = lifetime
        self.factory = factory
    }
}
