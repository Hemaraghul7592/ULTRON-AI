/// Runtime storage for a service registration within the container.
///
/// `ServiceRecord` wraps an immutable `ServiceRegistration` with
/// container-managed metadata: a monotonically increasing registration
/// index and an optional cached singleton instance.
///
/// The registration index provides deterministic ordering for diagnostics
/// and testing. When a type is re-registered, a new `ServiceRecord` is
/// created with a new index — the old record is discarded.
public struct ServiceRecord {

    // MARK: - Properties

    /// The immutable registration configuration.
    public let registration: ServiceRegistration

    /// Monotonically increasing registration index.
    /// Assigned at registration time. Never changes.
    /// Used for deterministic diagnostics and testing.
    public let index: Int

    /// Cached singleton instance. `nil` until first resolution.
    /// Only meaningful when `registration.lifetime == .singleton`.
    public var cachedInstance: Any?

    // MARK: - Initialization

    /// Creates a new service record.
    ///
    /// - Parameters:
    ///   - registration: The immutable registration configuration.
    ///   - index: The registration index assigned by the container.
    ///   - cachedInstance: An optional pre-cached instance (nil at registration time).
    public init(
        registration: ServiceRegistration,
        index: Int,
        cachedInstance: Any? = nil
    ) {
        self.registration = registration
        self.index = index
        self.cachedInstance = cachedInstance
    }
}
