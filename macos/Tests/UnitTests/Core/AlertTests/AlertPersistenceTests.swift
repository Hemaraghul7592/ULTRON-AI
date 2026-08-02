import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite(.serialized) struct AlertPersistenceTests {
    @Test("Rules and triggered history restore after restart")
    func restartRestoresState() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let first = makeEngine(location)
        await first.restorePersistedState()
        let rule = AlertRule(name: "Always", category: .system, condition: .alwaysTrue)
        first.addRule(rule)
        _ = await first.evaluate(quotes: [:])
        let alert = try #require(await first.getRecent().first)
        await first.acknowledge(alertID: alert.id)
        await first.dismiss(alertID: alert.id)
        await first.updateAlertMetadata(alertID: alert.id, aiExplanation: "Persisted explanation")
        await first.flushPersistence()

        let second = makeEngine(location)
        await second.restorePersistedState()
        #expect(second.getRules().count == 1)
        let restored = try #require(await second.getRecent().first)
        #expect(restored.acknowledgedAt != nil)
        #expect(restored.dismissedAt != nil)
        #expect(restored.aiExplanation == "Persisted explanation")
    }

    @Test("Rule deletion persists")
    func ruleDeletion() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        let rule = AlertRule(name: "Delete", category: .system, condition: .alwaysTrue)
        engine.addRule(rule)
        engine.removeRule(id: rule.id)
        await engine.flushPersistence()

        let restarted = makeEngine(location)
        await restarted.restorePersistedState()
        #expect(restarted.getRules().isEmpty)
    }

    @Test("Rule modification persists")
    func ruleModification() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        let rule = AlertRule(name: "Before", category: .system, condition: .alwaysTrue)
        engine.addRule(rule)
        engine.updateRule(AlertRule(id: rule.id, name: "After", category: .system, condition: .alwaysTrue, enabled: false))
        await engine.flushPersistence()
        let restarted = makeEngine(location)
        await restarted.restorePersistedState()
        #expect(restarted.getRules().first?.name == "After")
        #expect(restarted.getRules().first?.enabled == false)
    }

    @Test("Missing storage restores clean state")
    func missingStorage() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getRules().isEmpty)
        #expect(await engine.alertCount() == 0)
    }

    @Test("Corrupt storage restores clean state")
    func corruptStorage() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        try Data("corrupt".utf8).write(to: location)
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getRules().isEmpty)
        #expect(await engine.alertCount() == 0)
    }

    @Test("Version mismatch does not load future state")
    func versionMismatch() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let envelope = AlertPersistenceEnvelope(version: 99, rules: [AlertRule(name: "Future", category: .system, condition: .alwaysTrue)], history: [])
        try JSONEncoder().encode(envelope).write(to: location)
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getRules().isEmpty)
    }

    @Test("Invalid replacement preserves valid state")
    func atomicRecovery() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let storage = FileAlertStorage(fileURL: location)
        let valid = AlertPersistenceEnvelope(rules: [AlertRule(name: "Valid", category: .system, condition: .alwaysTrue)], history: [])
        try await storage.saveState(valid.rules, history: valid.history)
        let partialURL = location.deletingLastPathComponent().appendingPathComponent(".alerts.json.partial")
        try Data("partial-write".utf8).write(to: partialURL)
        let loaded = try await storage.loadRules()
        #expect(loaded.first?.name == "Valid")
    }

    @Test("Multiple rules persist")
    func multipleRules() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        for index in 0..<10 { engine.addRule(AlertRule(name: "Rule \(index)", category: .system, condition: .alwaysTrue)) }
        await engine.flushPersistence()
        let restarted = makeEngine(location)
        await restarted.restorePersistedState()
        #expect(restarted.getRules().count == 10)
    }

    private func makeEngine(_ location: URL) -> AlertEngine {
        AlertEngine(manager: AlertManager(), storage: FileAlertStorage(fileURL: location), logger: Logger(configuration: .init(minimumLevel: .error)))
    }

    private func temporaryLocation() throws -> URL {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("ULTRON-Alerts-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory.appendingPathComponent("alerts.json")
    }

    private func cleanup(_ location: URL) { try? FileManager.default.removeItem(at: location.deletingLastPathComponent()) }
}
