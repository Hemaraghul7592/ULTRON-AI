import Foundation
import OSLog

/// Writes log entries to the system console via `os_log`.
///
/// Entries appear in Console.app under the configured subsystem
/// and category, making them searchable and filterable alongside
/// other system logs.
///
/// This destination is suitable for development and production
/// alike. The system throttles excessive logging automatically.
public struct ConsoleDestination: LogDestination {

    // MARK: - Properties

    public let name = "Console"

    /// The `OSLog` instance used for writing.
    private let log: OSLog

    // MARK: - Initialization

    /// Creates a console destination that writes to the given subsystem.
    ///
    /// - Parameter subsystem: The subsystem identifier for Console.app
    ///   filtering (e.g., `"ai.ultron.app"`).
    public init(subsystem: String) {
        log = OSLog(subsystem: subsystem, category: "general")
    }

    // MARK: - LogDestination

    public func write(_ entry: LogEntry) async {
        let type = entry.level.osLogType
        os_log(type, log: log, "%{public}@", entry.message)
    }
}

private extension LogLevel {
    var osLogType: OSLogType {
        switch self {
        case .trace: .debug
        case .debug: .debug
        case .info: .info
        case .warning: .error
        case .error: .fault
        }
    }
}
