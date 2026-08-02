import Foundation
import Testing

@testable import ULTRON

// MARK: - Mock Provider

private actor MockFinancialProvider: FinancialProvider {
    let providerID: String
    let providerName: String
    let financialCapabilities: Set<FinancialCapability>
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []

    private var quoteValue: Quote
    private var ohlcvValue: [OHLCV]
    private var companyValue: CompanyProfile
    private var shouldFail = false

    init(id: String, name: String = "", capabilities: Set<FinancialCapability> = [.quotes]) {
        providerID = id; providerName = name.isEmpty ? id : name
        financialCapabilities = capabilities
        quoteValue = Quote(symbol: "AAPL", price: 150, change: 2, changePercent: 1.3, volume: 10_000_000, timestamp: Date())
        ohlcvValue = [OHLCV(symbol: "AAPL", open: 149, high: 151, low: 148, close: 150, volume: 5_000_000, timestamp: Date())]
        companyValue = CompanyProfile(symbol: "AAPL", name: "Apple Inc.", sector: "Technology")
    }

    func setQuote(_ q: Quote) { quoteValue = q }
    func setShouldFail(_ f: Bool) { shouldFail = f }
    func setOHLCV(_ o: [OHLCV]) { ohlcvValue = o }

    func initialize() async throws {}
    func healthCheck() async -> HealthStatus { shouldFail ? .unhealthy : .healthy }
    func shutdown() async {}

    func fetchQuote(symbol: String) async throws -> Quote {
        if shouldFail { throw FinancialError.symbolNotFound(symbol) }
        return quoteValue
    }
    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        if shouldFail { throw FinancialError.symbolNotFound(symbol) }
        return ohlcvValue
    }
    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        if shouldFail { throw FinancialError.symbolNotFound(symbol) }
        return companyValue
    }
    func fetchIndices() async throws -> [MarketIndex] { [] }
    func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }

    func execute(request: any Sendable) async throws -> any Sendable { quoteValue }
}

// MARK: - FinancialModels Tests

@Suite struct FinancialModelsTests {
    @Test("Quote is Equatable") func testQuoteEquatable() {
        let a = Quote(symbol: "A", price: 100, change: 1, changePercent: 1, volume: 1000, timestamp: Date(timeIntervalSince1970: 0))
        let b = Quote(symbol: "A", price: 100, change: 1, changePercent: 1, volume: 1000, timestamp: Date(timeIntervalSince1970: 0))
        #expect(a == b)
    }

    @Test("Quote is Codable") func testQuoteCodable() throws {
        let q = Quote(symbol: "AAPL", price: 150, change: 2, changePercent: 1.3, volume: 10_000_000, timestamp: Date(timeIntervalSince1970: 1000))
        let data = try JSONEncoder().encode(q)
        let decoded = try JSONDecoder().decode(Quote.self, from: data)
        #expect(decoded.symbol == "AAPL")
        #expect(decoded.price == 150)
    }

    @Test("CompanyProfile stores all fields") func testCompanyProfile() {
        let c = CompanyProfile(symbol: "AAPL", name: "Apple Inc.", sector: "Technology", marketCap: 2_000_000_000_000)
        #expect(c.name == "Apple Inc.")
        #expect(c.marketCap == 2_000_000_000_000)
    }

    @Test("OHLCVRange has expected cases") func testOHLCVRange() {
        #expect(OHLCVRange.allCases.count == 9)
        #expect(OHLCVRange.oneDay.rawValue == "1d")
    }
}

// MARK: - FinancialCache Tests

@Suite struct FinancialCacheTests {
    @Test("Cache miss returns nil") func testMiss() async {
        let cache = FinancialCache<String, String>()
        #expect(await cache.get("key") == nil)
    }

    @Test("Cache hit returns value") func testHit() async {
        let cache = FinancialCache<String, String>()
        await cache.set("key", value: "value")
        #expect(await cache.get("key") == "value")
    }

    @Test("Cache expires after TTL") func testExpiry() async {
        let cache = FinancialCache<String, String>(defaultTTL: 0)
        await cache.set("key", value: "expired")
        #expect(await cache.get("key") == nil)
    }

    @Test("Cache tracks hits and misses") func testStats() async {
        let cache = FinancialCache<String, String>(defaultTTL: 60)
        _ = await cache.get("a")
        await cache.set("b", value: "x")
        _ = await cache.get("b")
        #expect(await cache.misses == 1)
        #expect(await cache.hits == 1)
    }

    @Test("Cache clear removes all") func testClear() async {
        let cache = FinancialCache<String, String>()
        await cache.set("a", value: "1")
        await cache.clear()
        #expect(await cache.count == 0)
    }
}

// MARK: - FinancialRegistry Tests

@Suite struct FinancialRegistryTests {
    @Test("Register and query by capability") func testCapabilityQuery() {
        var reg = FinancialRegistry()
        reg.register(providerID: "p1", capabilities: [.quotes, .ohlcv], priority: 0)
        reg.register(providerID: "p2", capabilities: [.companyProfile], priority: 1)
        #expect(reg.providers(for: .quotes) == ["p1"])
        #expect(reg.providers(for: .companyProfile) == ["p2"])
    }

    @Test("Providers sorted by priority") func testPrioritySort() {
        var reg = FinancialRegistry()
        reg.register(providerID: "low", capabilities: [.quotes], priority: 10)
        reg.register(providerID: "high", capabilities: [.quotes], priority: 0)
        #expect(reg.providers(for: .quotes) == ["high", "low"])
    }

    @Test("Unregister removes provider") func testUnregister() {
        var reg = FinancialRegistry()
        reg.register(providerID: "p1", capabilities: [.quotes])
        reg.unregister(providerID: "p1")
        #expect(reg.count == 0)
    }
}

// MARK: - FinancialEngine Tests

@MainActor
@Suite struct FinancialEngineTests {

    @Test("Register and retrieve providers") func testRegistration() async {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test")
        await engine.registerProvider(p)
        #expect(engine.registeredProviderIDs() == ["test"])
    }

    @Test("Fetch quote returns data") func testFetchQuote() async throws {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test")
        await engine.registerProvider(p)
        engine.updateRegistry(for: p, capabilities: [.quotes])

        let quote = try await engine.fetchQuote(symbol: "AAPL")
        #expect(quote.symbol == "AAPL")
        #expect(quote.price == 150)
    }

    @Test("Fetch quote caches result") func testQuoteCache() async throws {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test")
        await engine.registerProvider(p)
        engine.updateRegistry(for: p, capabilities: [.quotes])

        _ = try await engine.fetchQuote(symbol: "AAPL")
        let stats = await engine.cacheStats()
        let quoteStats = stats.first { $0.name == "quotes" }
        #expect(quoteStats?.entries == 1)
    }

    @Test("Fetch OHLCV returns data") func testFetchOHLCV() async throws {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test", capabilities: [.quotes, .ohlcv])
        await engine.registerProvider(p)
        engine.updateRegistry(for: p, capabilities: [.quotes, .ohlcv])

        let bars = try await engine.fetchOHLCV(symbol: "AAPL")
        #expect(bars.count == 1)
        #expect(bars[0].close == 150)
    }

    @Test("Fetch company profile") func testFetchCompany() async throws {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test", capabilities: [.companyProfile])
        await engine.registerProvider(p)
        engine.updateRegistry(for: p, capabilities: [.companyProfile])

        let profile = try await engine.fetchCompanyProfile(symbol: "AAPL")
        #expect(profile.name == "Apple Inc.")
    }

    @Test("Provider not found throws") func testNoProvider() async {
        let engine = makeEngine()
        do {
            _ = try await engine.fetchQuote(symbol: "AAPL")
            Issue.record("Expected throw")
        } catch let e as FinancialError {
            if case .providerNotAvailable = e {} else { Issue.record("Wrong error: \(e)") }
        } catch { Issue.record("Unexpected: \(error)") }
    }

    @Test("Clear cache removes entries") func testClearCache() async throws {
        let engine = makeEngine()
        let p = MockFinancialProvider(id: "test", capabilities: [.quotes])
        await engine.registerProvider(p)
        engine.updateRegistry(for: p, capabilities: [.quotes])
        _ = try await engine.fetchQuote(symbol: "AAPL")
        await engine.clearCache()
        let stats = await engine.cacheStats()
        #expect(stats.allSatisfy { $0.entries == 0 })
    }

    @Test("Provider registry returns supported capabilities") func testRegistryCapabilities() {
        let engine = makeEngine()
        engine.updateRegistry(for: MockFinancialProvider(id: "test", capabilities: [.quotes, .news]), capabilities: [.quotes, .news])
        #expect(engine.providers(for: .quotes).count == 1)
        #expect(engine.providers(for: .technicals).isEmpty)
    }

    private func makeEngine() -> FinancialEngine {
        FinancialEngine(config: .init(quoteCacheTTL: 999), logger: Logger(configuration: .init(minimumLevel: .error)))
    }
}
