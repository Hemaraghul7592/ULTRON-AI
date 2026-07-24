import Foundation

/// An immutable record of a single log event.
///
/// Every call to the logger produces one `LogEntry`. Entries capture
/// the full context of the log event: when it occurred, how severe it
/// was, what subsystem produced it, where in the source code it came
/// from, and any structured metadata the caller attached.
///
/// Entries are value types and can be freely copied, compared, and
/// serialized without side effects.
public struct LogEntry: Codable, Equatable, Sendable {

    // MARK: - Properties

    /// The date and time the entry was created.
    public let timestamp: Date

    /// The severity level of the message.
    public let level: LogLevel

    /// The log message text.
    public let message: String

    /// The subsystem that produced this entry (e.g., `"ai.ultron.di"`).
    public let subsystem: String

    /// An optional category within the subsystem (e.g., `"resolution"`).
    public let category: String

    /// Optional structured key-value metadata.
    public let metadata: [String: String]

    /// The source file where the log call originated.
    public let sourceFile: String

    /// The function name where the log call originated.
    public let sourceFunction: String

    /// The line number where the log call originated.
    public let sourceLine: Int

    /// A human-readable name for the current thread.
    public let threadName: String

    // MARK: - Initialization

    /// Creates a log entry with the given values.
    ///
    /// - Parameters:
    ///   - timestamp: When the entry was created.
    ///   - level: The severity level.
    ///   - message: The log message text.
    ///   - subsystem: The subsystem identifier.
    ///   - category: An optional category.
    ///   - metadata: Optional key-value metadata.
    ///   - sourceFile: The originating source file.
    ///   - sourceFunction: The originating function.
    ///   - sourceLine: The originating line number.
    public init(
        timestamp: Date,
        level: LogLevel,
        message: String,
        subsystem: String,
        category: String = "",
        metadata: [String: String] = [:],
        sourceFile: String = "",
        sourceFunction: String = "",
        sourceLine: Int = 0,
        threadName: String = ""
    ) {
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.subsystem = subsystem
        self.category = category
        self.metadata = metadata
        self.sourceFile = sourceFile
        self.sourceFunction = sourceFunction
        self.sourceLine = sourceLine
        self.threadName = threadName
    }
}
