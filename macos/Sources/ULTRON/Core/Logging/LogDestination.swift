/// A destination for structured log entries.
///
/// Conforming types receive formatted or raw log entries and write
/// them to a specific output: the console, a file, a network service,
/// or any other sink.
///
/// Destinations are called sequentially by the logger on a
/// best-effort basis. A failing destination must not prevent other
/// destinations from receiving the entry.
///
/// Conforming types must be `Sendable` so they can be held by the
/// logger actor.
public protocol LogDestination: Sendable {

    /// The human-readable name of this destination for diagnostics.
    var name: String { get }

    /// Writes a log entry to this destination.
    ///
    /// Implementations should handle their own errors internally.
    /// The logger does not retry failed writes.
    ///
    /// - Parameter entry: The formatted or raw log entry to write.
    func write(_ entry: LogEntry) async
}
