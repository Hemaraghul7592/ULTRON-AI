import Foundation

/// The central logging service for ULTRON.
///
/// `Logger` accepts log messages at various severity levels and
/// delivers them to all configured destinations. Messages below
/// the configured minimum level are silently dropped.
///
/// ## Thread Safety
///
/// `Logger` is an actor. All logging calls are serialized and
/// safe to call from any concurrency domain.
///
/// ## Usage
/// ```swift
/// let logger = Logger(configuration: .init(subsystem: "ai.ultron.di"))
/// await logger.info("Container initialized", metadata: ["services": "12"])
/// ```
public actor Logger {
    // MARK: - Properties

    /// The logger's immutable configuration.
    public let configuration: LoggerConfiguration

    // MARK: - Initialization

    /// Creates a logger with the given configuration.
    ///
    /// - Parameter configuration: The immutable configuration.
    public init(configuration: LoggerConfiguration = .init()) {
        self.configuration = configuration
    }

    // MARK: - Public API

    /// Logs a message at the `.trace` level.
    public func trace(
        _ message: String,
        metadata: [String: String] = [:],
        sourceFile: String = #fileID,
        sourceFunction: String = #function,
        sourceLine: Int = #line
    ) async {
        await log(.trace, message, metadata: metadata, sourceFile: sourceFile, sourceFunction: sourceFunction, sourceLine: sourceLine)
    }

    /// Logs a message at the `.debug` level.
    public func debug(
        _ message: String,
        metadata: [String: String] = [:],
        sourceFile: String = #fileID,
        sourceFunction: String = #function,
        sourceLine: Int = #line
    ) async {
        await log(.debug, message, metadata: metadata, sourceFile: sourceFile, sourceFunction: sourceFunction, sourceLine: sourceLine)
    }

    /// Logs a message at the `.info` level.
    public func info(
        _ message: String,
        metadata: [String: String] = [:],
        sourceFile: String = #fileID,
        sourceFunction: String = #function,
        sourceLine: Int = #line
    ) async {
        await log(.info, message, metadata: metadata, sourceFile: sourceFile, sourceFunction: sourceFunction, sourceLine: sourceLine)
    }

    /// Logs a message at the `.warning` level.
    public func warning(
        _ message: String,
        metadata: [String: String] = [:],
        sourceFile: String = #fileID,
        sourceFunction: String = #function,
        sourceLine: Int = #line
    ) async {
        await log(.warning, message, metadata: metadata, sourceFile: sourceFile, sourceFunction: sourceFunction, sourceLine: sourceLine)
    }

    /// Logs a message at the `.error` level.
    public func error(
        _ message: String,
        metadata: [String: String] = [:],
        sourceFile: String = #fileID,
        sourceFunction: String = #function,
        sourceLine: Int = #line
    ) async {
        await log(.error, message, metadata: metadata, sourceFile: sourceFile, sourceFunction: sourceFunction, sourceLine: sourceLine)
    }

    // MARK: - Internal

    /// Creates and delivers a log entry if the level meets the minimum.
    private func log(
        _ level: LogLevel,
        _ message: String,
        metadata: [String: String],
        sourceFile: String,
        sourceFunction: String,
        sourceLine: Int
    ) async {
        guard level >= configuration.minimumLevel else { return }

        let entry = LogEntry(
            timestamp: Date(),
            level: level,
            message: message,
            subsystem: configuration.subsystem,
            metadata: metadata,
            sourceFile: configuration.captureSourceLocation ? sourceFile : "",
            sourceFunction: configuration.captureSourceLocation ? sourceFunction : "",
            sourceLine: configuration.captureSourceLocation ? sourceLine : 0,
            threadName: ""
        )

        for destination in configuration.destinations {
            await destination.write(entry)
        }
    }
}
