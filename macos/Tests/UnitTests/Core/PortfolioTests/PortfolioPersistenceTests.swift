import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite(.serialized) struct PortfolioPersistenceTests {
    @Test("Create and restart restores portfolio state")
    func createAndRestart() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let first = makeEngine(location)
        await first.restorePersistedState()
        let portfolio = first.createPortfolio(name: "Primary", description: "Long term", cash: 1_000)
        try first.addTransaction(to: portfolio.id, Transaction(type: .buy, symbol: "TEST", quantity: 2, price: 100))
        let watchlist = first.createWatchlist(name: "Core")
        try first.addToWatchlist(watchlistID: watchlist.id, symbol: "TEST")
        await first.flushPersistence()

        let second = makeEngine(location)
        await second.restorePersistedState()
        let restored = try #require(second.getPortfolio(id: portfolio.id))
        #expect(restored.name == "Primary")
        #expect(restored.cashBalance == 800)
        #expect(restored.holdings.first?.quantity == 2)
        #expect(restored.transactions.count == 1)
        #expect(second.getAllWatchlists().first?.symbols.first?.symbol == "TEST")
    }

    @Test("Rename and delete persist across restart")
    func renameAndDelete() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        let retained = engine.createPortfolio(name: "Before", cash: 10)
        let removed = engine.createPortfolio(name: "Removed", cash: 20)
        engine.renamePortfolio(id: retained.id, name: "After", description: "Updated")
        engine.deletePortfolio(id: removed.id)
        await engine.flushPersistence()

        let restarted = makeEngine(location)
        await restarted.restorePersistedState()
        #expect(restarted.getPortfolio(id: retained.id)?.name == "After")
        #expect(restarted.getPortfolio(id: retained.id)?.description == "Updated")
        #expect(restarted.getPortfolio(id: removed.id) == nil)
    }

    @Test("Missing storage restores empty state")
    func missingStorage() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getAllPortfolios().isEmpty)
        #expect(engine.getAllWatchlists().isEmpty)
    }

    @Test("Corrupted storage restores empty state without crashing")
    func corruptedStorage() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        try Data("not-json".utf8).write(to: location)
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getAllPortfolios().isEmpty)
    }

    @Test("Version mismatch restores empty state")
    func versionMismatch() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let envelope = PortfolioPersistenceEnvelope(version: 99, portfolios: [Portfolio(name: "Future")], watchlists: [])
        try JSONEncoder().encode(envelope).write(to: location)
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        #expect(engine.getAllPortfolios().isEmpty)
    }

    @Test("Invalid replacement does not overwrite valid storage")
    func atomicRecovery() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let storage = FilePortfolioStorage(fileURL: location)
        let original = PortfolioPersistenceEnvelope(portfolios: [Portfolio(name: "Valid")], watchlists: [])
        try await storage.save(original, forKey: "portfolio-state")
        let invalidVersion = PortfolioPersistenceEnvelope(version: 2, portfolios: [Portfolio(name: "Invalid")], watchlists: [])
        try await storage.save(invalidVersion, forKey: "portfolio-state")
        let loaded: PortfolioPersistenceEnvelope? = try await storage.load(forKey: "portfolio-state")
        #expect(loaded?.portfolios.first?.name == "Valid")
    }

    @Test("Multiple portfolios and queued saves persist")
    func multiplePortfolios() async throws {
        let location = try temporaryLocation()
        defer { cleanup(location) }
        let engine = makeEngine(location)
        await engine.restorePersistedState()
        for index in 0..<10 { _ = engine.createPortfolio(name: "Portfolio \(index)", cash: Double(index)) }
        await engine.flushPersistence()
        let restarted = makeEngine(location)
        await restarted.restorePersistedState()
        #expect(restarted.getAllPortfolios().count == 10)
    }

    private func makeEngine(_ location: URL) -> PortfolioEngine {
        PortfolioEngine(storage: FilePortfolioStorage(fileURL: location), logger: Logger(configuration: .init(minimumLevel: .error)))
    }

    private func temporaryLocation() throws -> URL {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent("ULTRON-Portfolio-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        return directory.appendingPathComponent("portfolios.json")
    }

    private func cleanup(_ location: URL) {
        try? FileManager.default.removeItem(at: location.deletingLastPathComponent())
    }
}
