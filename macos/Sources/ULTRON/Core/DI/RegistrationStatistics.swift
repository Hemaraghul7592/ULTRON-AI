/// Immutable statistics about container registrations.
///
/// Exposes counts without revealing internal storage or factory closures.
/// Created by `ContainerDiagnostics.totalRegistrations()`.
public struct RegistrationStatistics: Sendable {

    // MARK: - Properties

    /// The number of currently active (non-overwritten) registrations.
    public let activeCount: Int

    /// The total number of registrations ever made, including overwrites.
    public let totalCount: Int

    /// The number of registrations that have been overwritten.
    /// Computed as `totalCount - activeCount`.
    public var overwrittenCount: Int {
        totalCount - activeCount
    }

    /// Whether any registrations have been overwritten.
    public var hasOverwrites: Bool {
        overwrittenCount > 0
    }
}
