import Foundation
import Testing

@testable import ULTRON

// MARK: - LogLevel Tests

@Suite struct LogLevelTests {

    @Test("LogLevel has five cases in correct order")
    func testAllCases() {
        let cases = LogLevel.allCases
        #expect(cases.count == 5)
        #expect(cases[0] == .trace)
        #expect(cases[1] == .debug)
        #expect(cases[2] == .info)
        #expect(cases[3] == .warning)
        #expect(cases[4] == .error)
    }

    @Test("LogLevel is comparable")
    func testComparable() {
        #expect(LogLevel.trace < LogLevel.debug)
        #expect(LogLevel.debug < LogLevel.info)
        #expect(LogLevel.info < LogLevel.warning)
        #expect(LogLevel.warning < LogLevel.error)
    }

    @Test("LogLevel has descriptive labels")
    func testDescriptions() {
        #expect(LogLevel.trace.description == "TRACE")
        #expect(LogLevel.debug.description == "DEBUG")
        #expect(LogLevel.info.description == "INFO")
        #expect(LogLevel.warning.description == "WARNING")
        #expect(LogLevel.error.description == "ERROR")
    }

    @Test("LogLevel is Codable")
    func testCodable() throws {
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        let data = try encoder.encode(LogLevel.warning)
        let decoded = try decoder.decode(LogLevel.self, from: data)
        #expect(decoded == .warning)
    }

    @Test("LogLevel conforms to Sendable")
    func testSendable() {
        let level: any Sendable = LogLevel.info
        _ = level
    }
}

// MARK: - LogEntry Tests

@Suite struct LogEntryTests {

    @Test("LogEntry stores all properties")
    func testProperties() {
        let now = Date()
        let entry = LogEntry(
            timestamp: now,
            level: .info,
            message: "test",
            subsystem: "sub",
            category: "cat",
            metadata: ["key": "value"],
            sourceFile: "File.swift",
            sourceFunction: "func()",
            sourceLine: 42,
            threadName: "main"
        )

        #expect(entry.timestamp == now)
        #expect(entry.level == .info)
        #expect(entry.message == "test")
        #expect(entry.subsystem == "sub")
        #expect(entry.category == "cat")
        #expect(entry.metadata["key"] == "value")
        #expect(entry.sourceFile == "File.swift")
        #expect(entry.sourceFunction == "func()")
        #expect(entry.sourceLine == 42)
        #expect(entry.threadName == "main")
    }

    @Test("LogEntry defaults are sensible")
    func testDefaults() {
        let entry = LogEntry(
            timestamp: Date(),
            level: .debug,
            message: "",
            subsystem: ""
        )
        #expect(entry.category == "")
        #expect(entry.metadata.isEmpty)
        #expect(entry.sourceFile == "")
        #expect(entry.sourceLine == 0)
    }

    @Test("LogEntry is Equatable")
    func testEquatable() {
        let now = Date()
        let a = LogEntry(timestamp: now, level: .info, message: "a", subsystem: "s")
        let b = LogEntry(timestamp: now, level: .info, message: "a", subsystem: "s")
        #expect(a == b)
    }

    @Test("LogEntry is Codable")
    func testCodable() throws {
        let entry = LogEntry(
            timestamp: Date(timeIntervalSince1970: 1000),
            level: .warning,
            message: "msg",
            subsystem: "sys",
            metadata: ["k": "v"]
        )
        let encoder = JSONEncoder()
        let decoder = JSONDecoder()
        let data = try encoder.encode(entry)
        let decoded = try decoder.decode(LogEntry.self, from: data)
        #expect(decoded.message == "msg")
        #expect(decoded.level == .warning)
        #expect(decoded.subsystem == "sys")
        #expect(decoded.metadata["k"] == "v")
    }

    @Test("LogEntry conforms to Sendable")
    func testSendable() {
        let entry = LogEntry(timestamp: Date(), level: .info, message: "", subsystem: "")
        let sendable: any Sendable = entry
        _ = sendable
    }
}

// MARK: - Mock Destination

private actor MockDestination: LogDestination {
    let name = "Mock"
    private(set) var entries: [LogEntry] = []

    func write(_ entry: LogEntry) async {
        entries.append(entry)
    }

    func getEntries() -> [LogEntry] {
        entries
    }
}

// MARK: - LogFormatter Tests

@Suite struct LogFormatterTests {

    @Test("PlainTextFormatter produces timestamped output")
    func testPlainTextFormatter() {
        let formatter = PlainTextFormatter()
        let entry = LogEntry(
            timestamp: Date(timeIntervalSince1970: 1750000000),
            level: .info,
            message: "hello",
            subsystem: "ai.test"
        )
        let output = formatter.format(entry)
        #expect(output.contains("INFO"))
        #expect(output.contains("ai.test"))
        #expect(output.contains("hello"))
    }

    @Test("PlainTextFormatter includes metadata")
    func testPlainTextFormatterMetadata() {
        let formatter = PlainTextFormatter()
        let entry = LogEntry(
            timestamp: Date(),
            level: .debug,
            message: "msg",
            subsystem: "s",
            metadata: ["key": "val"]
        )
        let output = formatter.format(entry)
        #expect(output.contains("key=val"))
    }

    @Test("JSONFormatter produces valid JSON")
    func testJSONFormatter() {
        let formatter = JSONFormatter()
        let entry = LogEntry(
            timestamp: Date(timeIntervalSince1970: 1000),
            level: .error,
            message: "fail",
            subsystem: "test"
        )
        let output = formatter.format(entry)
        #expect(output.contains("\"fail\""))
        #expect(output.contains("\"level\":\"error\""))
        #expect(output.contains("{"))
        #expect(output.contains("}"))
    }
}

// MARK: - Console Destination Tests

@Suite struct ConsoleDestinationTests {

    @Test("Console destination has correct name")
    func testName() {
        let dest = ConsoleDestination(subsystem: "test")
        #expect(dest.name == "Console")
    }

    @Test("Console destination writes without throwing")
    func testWrite() async {
        let dest = ConsoleDestination(subsystem: "test")
        let entry = LogEntry(timestamp: Date(), level: .info, message: "console test", subsystem: "test")
        await dest.write(entry)
    }
}

// MARK: - File Destination Tests

@Suite struct FileDestinationTests {

    @Test("File destination writes entries to file")
    func testFileWrite() async throws {
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("ultron-test-\(UUID().uuidString).log")
        defer { try? FileManager.default.removeItem(at: tempURL) }

        let dest = FileDestination(fileURL: tempURL)
        let entry = LogEntry(timestamp: Date(), level: .info, message: "file test", subsystem: "test")
        await dest.write(entry)

        let contents = try String(contentsOf: tempURL, encoding: .utf8)
        #expect(contents.contains("file test"))
    }

    @Test("File destination appends multiple entries")
    func testFileAppend() async throws {
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("ultron-test-\(UUID().uuidString).log")
        defer { try? FileManager.default.removeItem(at: tempURL) }

        let dest = FileDestination(fileURL: tempURL)
        await dest.write(LogEntry(timestamp: Date(), level: .info, message: "first", subsystem: "test"))
        await dest.write(LogEntry(timestamp: Date(), level: .info, message: "second", subsystem: "test"))

        let contents = try String(contentsOf: tempURL, encoding: .utf8)
        #expect(contents.contains("first"))
        #expect(contents.contains("second"))
    }
}

// MARK: - Composite Destination Tests

@Suite struct CompositeDestinationTests {

    @Test("Composite destination forwards to all children")
    func testForwarding() async {
        let mock1 = MockDestination()
        let mock2 = MockDestination()
        let composite = CompositeDestination(children: [mock1, mock2])

        let entry = LogEntry(timestamp: Date(), level: .info, message: "composite", subsystem: "test")
        await composite.write(entry)

        let entries1 = await mock1.getEntries()
        let entries2 = await mock2.getEntries()
        #expect(entries1.count == 1)
        #expect(entries2.count == 1)
        #expect(entries1[0].message == "composite")
        #expect(entries2[0].message == "composite")
    }

    @Test("Composite destination with empty children does not crash")
    func testEmptyChildren() async {
        let composite = CompositeDestination(children: [])
        let entry = LogEntry(timestamp: Date(), level: .info, message: "nobody", subsystem: "test")
        await composite.write(entry)
    }
}

// MARK: - Logger Tests

@Suite struct LoggerTests {

    @Test("Logger with mock destination receives entries")
    func testLogging() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(
            minimumLevel: .debug,
            destinations: [mock]
        )
        let logger = Logger(configuration: config)

        await logger.info("test message")
        let entries = await mock.getEntries()
        #expect(entries.count == 1)
        #expect(entries[0].message == "test message")
        #expect(entries[0].level == .info)
    }

    @Test("Logger drops messages below minimum level")
    func testFiltering() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(
            minimumLevel: .warning,
            destinations: [mock]
        )
        let logger = Logger(configuration: config)

        await logger.debug("should drop")
        await logger.info("should drop")
        await logger.warning("should keep")
        await logger.error("should keep")

        let entries = await mock.getEntries()
        #expect(entries.count == 2)
        #expect(entries[0].level == .warning)
        #expect(entries[1].level == .error)
    }

    @Test("Logger captures source location")
    func testSourceLocation() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(
            destinations: [mock],
            captureSourceLocation: true
        )
        let logger = Logger(configuration: config)
        await logger.info("loc test")

        let entries = await mock.getEntries()
        #expect(entries.count == 1)
        #expect(!entries[0].sourceFile.isEmpty)
        #expect(entries[0].sourceLine > 0)
    }

    @Test("Logger suppresses source location when disabled")
    func testSourceLocationDisabled() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(
            destinations: [mock],
            captureSourceLocation: false
        )
        let logger = Logger(configuration: config)
        await logger.info("no loc")

        let entries = await mock.getEntries()
        #expect(entries[0].sourceFile == "")
        #expect(entries[0].sourceLine == 0)
    }

    @Test("Logger includes metadata in entries")
    func testMetadata() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(destinations: [mock])
        let logger = Logger(configuration: config)

        await logger.info("meta", metadata: ["key": "value"])
        let entries = await mock.getEntries()
        #expect(entries[0].metadata["key"] == "value")
    }

    @Test("Logger supports all five levels")
    func testAllLevels() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(minimumLevel: .trace, destinations: [mock])
        let logger = Logger(configuration: config)

        await logger.trace("t")
        await logger.debug("d")
        await logger.info("i")
        await logger.warning("w")
        await logger.error("e")

        let entries = await mock.getEntries()
        #expect(entries.count == 5)
        #expect(entries.map(\.level) == [.trace, .debug, .info, .warning, .error])
    }
}

// MARK: - LoggerConfiguration Tests

@Suite struct LoggerConfigurationTests {

    @Test("Default configuration has sensible values")
    func testDefaults() {
        let config = LoggerConfiguration()
        #expect(config.minimumLevel == .info)
        #expect(config.subsystem == "ai.ultron.app")
        #expect(config.destinations.isEmpty)
        #expect(config.captureSourceLocation == true)
    }

    @Test("Custom configuration stores values correctly")
    func testCustom() {
        let mock = MockDestination()
        let config = LoggerConfiguration(
            minimumLevel: .error,
            subsystem: "custom",
            destinations: [mock],
            captureSourceLocation: false
        )
        #expect(config.minimumLevel == .error)
        #expect(config.subsystem == "custom")
        #expect(config.destinations.count == 1)
        #expect(config.captureSourceLocation == false)
    }
}

// MARK: - Thread Safety Tests

@Suite struct LoggerThreadSafetyTests {

    @Test("Logger handles concurrent writes without data loss")
    func testConcurrentWrites() async {
        let mock = MockDestination()
        let config = LoggerConfiguration(destinations: [mock])
        let logger = Logger(configuration: config)

        await withTaskGroup(of: Void.self) { group in
            for i in 0..<100 {
                group.addTask {
                    await logger.info("msg-\(i)")
                }
            }
        }

        let entries = await mock.getEntries()
        #expect(entries.count == 100)
    }
}
