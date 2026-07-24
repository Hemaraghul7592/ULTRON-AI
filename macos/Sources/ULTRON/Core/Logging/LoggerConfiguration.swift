/// Configuration for a `Logger` instance.
///
/// Specifies the minimum severity level, subsystem identifier,
/// destination list, and whether source location capture is
/// enabled. Configuration is immutable after creation.
public struct LoggerConfiguration: Sendable {

    // MARK: - Properties

    /// The minimum log level. Messages below this level are
    /// silently dropped. Defaults to `.info`.
    public let minimumLevel: LogLevel

    /// The subsystem identifier (e.g., `"ai.ultron.app"`).
    /// Appears in Console.app and log entries.
    public let subsystem: String

    /// The destinations that receive log entries.
    public let destinations: [any LogDestination]

    /// Whether to capture source file, function, and line
    /// information. Enabling this has a small performance cost.
    /// Defaults to `true` in debug builds, `false` otherwise.
    public let captureSourceLocation: Bool

    // MARK: - Initialization

    /// Creates a logger configuration.
    ///
    /// - Parameters:
    ///   - minimumLevel: The minimum severity to log.
    ///   - subsystem: The subsystem identifier.
    ///   - destinations: Where entries are written.
    ///   - captureSourceLocation: Whether to record source locations.
    public init(
        minimumLevel: LogLevel = .info,
        subsystem: String = "ai.ultron.app",
        destinations: [any LogDestination] = [],
        captureSourceLocation: Bool = true
    ) {
        self.minimumLevel = minimumLevel
        self.subsystem = subsystem
        self.destinations = destinations
        self.captureSourceLocation = captureSourceLocation
    }
}
