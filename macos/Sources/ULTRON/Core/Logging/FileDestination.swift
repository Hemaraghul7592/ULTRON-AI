import Foundation

/// Writes log entries to a local file.
///
/// Entries are appended as plain text lines. The file is created
/// if it does not exist.
///
/// File access is serialized through a `DispatchQueue` rather than
/// `NSLock` because `NSLock` is unavailable in Swift 6 async contexts.
public struct FileDestination: LogDestination {

    // MARK: - Properties

    public let name = "File"

    /// The file URL where entries are written.
    public let fileURL: URL

    /// The formatter used to convert entries to text lines.
    private let formatter: any LogEntryFormatter

    /// Serial queue for thread-safe file access.
    private let queue = DispatchQueue(label: "ai.ultron.file-destination")

    // MARK: - Initialization

    /// Creates a file destination.
    ///
    /// - Parameters:
    ///   - fileURL: The file to write entries to.
    ///   - formatter: The formatter for converting entries to text.
    public init(
        fileURL: URL,
        formatter: any LogEntryFormatter = PlainTextFormatter()
    ) {
        self.fileURL = fileURL
        self.formatter = formatter
        ensureFileExists()
    }

    // MARK: - LogDestination

    public func write(_ entry: LogEntry) async {
        let line = formatter.format(entry) + "\n"
        guard let data = line.data(using: .utf8) else { return }

        queue.sync {
            guard let handle = try? FileHandle(forWritingTo: fileURL) else { return }
            defer { try? handle.close() }
            _ = try? handle.seekToEnd()
            _ = try? handle.write(contentsOf: data)
        }
    }

    // MARK: - Helpers

    private func ensureFileExists() {
        if !FileManager.default.fileExists(atPath: fileURL.path) {
            FileManager.default.createFile(atPath: fileURL.path, contents: nil)
        }
    }
}
