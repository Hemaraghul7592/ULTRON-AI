/// The severity of a log message.
///
/// Levels are ordered from least to most severe. A logger configured
/// with a minimum level of `.info` will suppress `.debug` and `.trace`
/// messages while allowing `.info`, `.warning`, and `.error`.
///
/// Levels encode as lowercase strings for human-readable JSON output:
/// `"trace"`, `"debug"`, `"info"`, `"warning"`, `"error"`.
public enum LogLevel: String, CaseIterable, Comparable, Codable, Sendable, CustomStringConvertible {

    /// Extremely detailed diagnostic output.
    case trace = "trace"

    /// Detailed information useful during development and debugging.
    case debug = "debug"

    /// General operational messages. The default minimum level for
    /// production builds.
    case info = "info"

    /// Potentially harmful situations that do not prevent the
    /// application from functioning.
    case warning = "warning"

    /// Error conditions that prevent a specific operation from
    /// completing.
    case error = "error"

    // MARK: - CustomStringConvertible

    public var description: String {
        rawValue.uppercased()
    }

    // MARK: - Comparable

    /// Ordered by increasing severity.
    private var severity: Int {
        switch self {
        case .trace: 0
        case .debug: 1
        case .info: 2
        case .warning: 3
        case .error: 4
        }
    }

    public static func < (lhs: LogLevel, rhs: LogLevel) -> Bool {
        lhs.severity < rhs.severity
    }
}
