/// A lightweight, immutable snapshot of a container registration.
///
/// `RegistrationSnapshot` exposes only the information that external
/// callers and diagnostics need: the type name, lifetime policy, and
/// registration index. It deliberately hides internal details such as
/// factory closures, cached instances, and storage implementation.
///
/// Snapshots are created by `DependencyContainer.snapshot()` and are
/// suitable for debugging, logging, and test assertions.
public struct RegistrationSnapshot: Sendable {

    // MARK: - Properties

    /// A human-readable name for the registered type.
    /// Derived from the type's runtime metadata.
    public let typeName: String

    /// The lifetime policy at registration time.
    public let lifetime: ServiceLifetime

    /// The monotonically increasing registration index.
    /// Lower values were registered earlier.
    public let registrationIndex: Int

    // MARK: - Initialization

    /// Creates a snapshot with the given values.
    ///
    /// This initializer is used by tests and by `DependencyContainer.snapshot()`.
    /// External callers typically receive pre-built snapshots.
    ///
    /// - Parameters:
    ///   - typeName: A human-readable name for the registered type.
    ///   - lifetime: The lifetime policy at registration time.
    ///   - registrationIndex: The monotonically increasing registration index.
    public init(typeName: String, lifetime: ServiceLifetime, registrationIndex: Int) {
        self.typeName = typeName
        self.lifetime = lifetime
        self.registrationIndex = registrationIndex
    }

    /// Creates a snapshot from a `ServiceRecord`.
    ///
    /// This initializer is used internally by the container.
    /// External callers should use the public initializer.
    init(record: ServiceRecord) {
        self.typeName = record.registration.typeName
        self.lifetime = record.registration.lifetime
        self.registrationIndex = record.index
    }
}
