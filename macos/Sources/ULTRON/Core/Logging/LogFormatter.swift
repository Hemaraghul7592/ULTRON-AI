import Foundation

/// Converts a `LogEntry` into a formatted string for output.
///
/// Formatters separate the presentation of log data from its
/// collection. Different destinations can use different formatters:
/// plain text for files, structured JSON for network transport,
/// or colored output for terminal displays.
public protocol LogEntryFormatter: Sendable {
    func format(_ entry: LogEntry) -> String
}

/// Formats entries as timestamped plain text lines.
///
/// Output format:
/// ```
/// 2026-07-26T10:30:00Z [INFO ] [ai.ultron.di] Container initialized
/// ```
public struct PlainTextFormatter: LogEntryFormatter {

    /// Whether to include fractional seconds in timestamps.
    private let includeFractionalSeconds: Bool

    public init(includeFractionalSeconds: Bool = false) {
        self.includeFractionalSeconds = includeFractionalSeconds
    }

    public func format(_ entry: LogEntry) -> String {
        let formatter = ISO8601DateFormatter()
        if includeFractionalSeconds {
            formatter.formatOptions.insert(.withFractionalSeconds)
        }

        let timestamp = formatter.string(from: entry.timestamp)
        let level = entry.level.description.padding(toLength: 7, withPad: " ", startingAt: 0)
        let subsystem = "[\(entry.subsystem)]"
        var line = "\(timestamp) \(level) \(subsystem) \(entry.message)"

        if !entry.metadata.isEmpty {
            let meta = entry.metadata
                .map { "\($0.key)=\($0.value)" }
                .joined(separator: " ")
            line += " {\(meta)}"
        }

        return line
    }
}

/// Formats entries as JSON objects for machine consumption.
///
/// Output format:
/// ```json
/// {"timestamp":"...","level":"info","subsystem":"ai.ultron.di","message":"..."}
/// ```
public struct JSONFormatter: LogEntryFormatter {

    public init() {}

    public func format(_ entry: LogEntry) -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        guard let data = try? encoder.encode(entry),
              let string = String(data: data, encoding: .utf8)
        else {
            return "{}"
        }
        return string
    }
}
