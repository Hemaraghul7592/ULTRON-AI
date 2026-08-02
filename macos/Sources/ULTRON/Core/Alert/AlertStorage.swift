import Foundation

/// Pluggable persistence for alert rules.
/// Future: SwiftDataAlertStorage, SQLiteAlertStorage.
public protocol AlertStorage: Sendable {
    func saveRules(_ rules: [AlertRule]) async throws
    func loadRules() async throws -> [AlertRule]
    func saveHistory(_ alerts: [Alert]) async throws
    func loadHistory() async throws -> [Alert]
    func saveState(_ rules: [AlertRule], history: [Alert]) async throws
}

public extension AlertStorage {
    func saveState(_ rules: [AlertRule], history: [Alert]) async throws {
        try await saveRules(rules)
        try await saveHistory(history)
    }
}

/// In-memory storage for testing and development.
public actor InMemoryAlertStorage: AlertStorage {
    private var rules: [AlertRule] = []
    private var history: [Alert] = []

    public init() {}

    public func saveRules(_ r: [AlertRule]) async throws { rules = r }
    public func loadRules() async throws -> [AlertRule] { rules }
    public func saveHistory(_ a: [Alert]) async throws { history = a }
    public func loadHistory() async throws -> [Alert] { history }
}

public struct AlertPersistenceEnvelope: Codable, Sendable {
    public static let currentVersion = 1
    public let version: Int
    public let rules: [AlertRule]
    public let history: [Alert]

    public init(version: Int = AlertPersistenceEnvelope.currentVersion, rules: [AlertRule], history: [Alert]) {
        self.version = version; self.rules = rules; self.history = history
    }
}

public actor FileAlertStorage: AlertStorage {
    public let fileURL: URL

    public init(fileURL: URL = FileAlertStorage.defaultURL()) { self.fileURL = fileURL }

    public func saveState(_ rules: [AlertRule], history: [Alert]) async throws {
        let envelope = AlertPersistenceEnvelope(rules: rules, history: history)
        let data = try JSONEncoder().encode(envelope)
        _ = try JSONDecoder().decode(AlertPersistenceEnvelope.self, from: data)
        let directory = fileURL.deletingLastPathComponent()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let temporaryURL = directory.appendingPathComponent(".\(fileURL.lastPathComponent).\(UUID().uuidString).tmp")
        do {
            try data.write(to: temporaryURL, options: [.atomic])
            if FileManager.default.fileExists(atPath: fileURL.path) {
                _ = try FileManager.default.replaceItemAt(fileURL, withItemAt: temporaryURL)
            } else {
                try FileManager.default.moveItem(at: temporaryURL, to: fileURL)
            }
        } catch {
            try? FileManager.default.removeItem(at: temporaryURL)
            throw error
        }
    }

    public func saveRules(_ rules: [AlertRule]) async throws {
        let existing = loadEnvelope()
        try await saveState(rules, history: existing?.history ?? [])
    }

    public func saveHistory(_ alerts: [Alert]) async throws {
        let existing = loadEnvelope()
        try await saveState(existing?.rules ?? [], history: alerts)
    }

    public func loadRules() async throws -> [AlertRule] { loadEnvelope()?.rules ?? [] }
    public func loadHistory() async throws -> [Alert] { loadEnvelope()?.history ?? [] }

    public func remove(forKey key: String = "alert-state") async {
        try? FileManager.default.removeItem(at: fileURL)
    }

    public static func defaultURL() -> URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first ?? FileManager.default.temporaryDirectory
        return base.appendingPathComponent("ULTRON/Alerts.json")
    }

    private func loadEnvelope() -> AlertPersistenceEnvelope? {
        guard FileManager.default.fileExists(atPath: fileURL.path), let data = try? Data(contentsOf: fileURL), !data.isEmpty,
              let envelope = try? JSONDecoder().decode(AlertPersistenceEnvelope.self, from: data),
              envelope.version == AlertPersistenceEnvelope.currentVersion else { return nil }
        return envelope
    }
}
