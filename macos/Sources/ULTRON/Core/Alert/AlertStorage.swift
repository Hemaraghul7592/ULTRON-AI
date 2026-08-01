import Foundation

/// Pluggable persistence for alert rules.
/// Future: SwiftDataAlertStorage, SQLiteAlertStorage.
public protocol AlertStorage: Sendable {
    func saveRules(_ rules: [AlertRule]) async throws
    func loadRules() async throws -> [AlertRule]
    func saveHistory(_ alerts: [Alert]) async throws
    func loadHistory() async throws -> [Alert]
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
