import Foundation
import Testing

@testable import ULTRON

private actor RoutingProvider: FinancialProvider {
    let providerID: String
    let providerName: String
    let financialCapabilities: Set<FinancialCapability>
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []

    private var status: HealthStatus = .healthy
    private var failure: FinancialError?
    private(set) var quoteCalls = 0
    private(set) var healthCalls = 0

    init(id: String, capabilities: Set<FinancialCapability> = [.quotes]) {
        providerID = id
        providerName = id
        financialCapabilities = capabilities
    }

    func setHealth(_ status: HealthStatus) { self.status = status }
    func setFailure(_ failure: FinancialError?) { self.failure = failure }

    func initialize() async throws {}
    func healthCheck() async -> HealthStatus {
        healthCalls += 1
        return status
    }
    func execute(request: any Sendable) async throws -> any Sendable { "unused" }

    func fetchQuote(symbol: String) async throws -> Quote {
        quoteCalls += 1
        if let failure { throw failure }
        return Quote(symbol: symbol, price: 100, change: 1, changePercent: 1, volume: 1_000, timestamp: Date())
    }
    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { [] }
    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { CompanyProfile(symbol: symbol, name: providerID) }
    func fetchIndices() async throws -> [MarketIndex] { [] }
    func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
}

@MainActor
@Suite struct ProviderRoutingTests {
    @Test("Unsupported capability is never selected")
    func unsupportedCapabilityIsNeverSelected() async {
        let engine = makeEngine()
        let provider = RoutingProvider(id: "quotes-only", capabilities: [.quotes])
        await provider.setFailure(.invalidResponse("must not be called"))
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.ohlcv])

        do {
            _ = try await engine.fetchOHLCV(symbol: "AAPL")
            Issue.record("Expected providerNotAvailable")
        } catch let error as FinancialError {
            guard case .providerNotAvailable("ohlcv") = error else { Issue.record("Wrong error: \(error)"); return }
        } catch { Issue.record("Unexpected error: \(error)") }
        #expect(await provider.quoteCalls == 0)
        #expect(engine.metrics(for: "quotes-only")?.capabilityMismatchCount == 1)
    }

    @Test("Disabled provider is skipped")
    func disabledProviderIsSkipped() async throws {
        let engine = makeEngine()
        let disabled = RoutingProvider(id: "disabled")
        let enabled = RoutingProvider(id: "enabled")
        await engine.registerProvider(disabled)
        await engine.registerProvider(enabled)
        engine.updateRegistry(for: disabled, capabilities: [.quotes], priority: 0, enabled: false)
        engine.updateRegistry(for: enabled, capabilities: [.quotes], priority: 1)

        let quote = try await engine.fetchQuote(symbol: "AAPL")
        #expect(quote.symbol == "AAPL")
        #expect(await disabled.quoteCalls == 0)
        #expect(await enabled.quoteCalls == 1)
        #expect(engine.metrics(for: "disabled")?.skippedCount == 1)
    }

    @Test("Unhealthy provider is skipped")
    func unhealthyProviderIsSkipped() async throws {
        let engine = makeEngine()
        let unhealthy = RoutingProvider(id: "unhealthy")
        let healthy = RoutingProvider(id: "healthy")
        await unhealthy.setHealth(.unhealthy)
        await engine.registerProvider(unhealthy)
        await engine.registerProvider(healthy)
        engine.updateRegistry(for: unhealthy, capabilities: [.quotes], priority: 0)
        engine.updateRegistry(for: healthy, capabilities: [.quotes], priority: 1)

        _ = try await engine.fetchQuote(symbol: "AAPL")
        #expect(await unhealthy.quoteCalls == 0)
        #expect(await unhealthy.healthCalls == 1)
        #expect(await healthy.quoteCalls == 1)
        #expect(engine.metrics(for: "unhealthy")?.healthFailureCount == 1)
    }

    @Test("Highest priority compatible provider is selected")
    func highestPriorityIsSelected() async throws {
        let engine = makeEngine()
        let low = RoutingProvider(id: "low")
        let high = RoutingProvider(id: "high")
        await engine.registerProvider(low)
        await engine.registerProvider(high)
        engine.updateRegistry(for: low, capabilities: [.quotes], priority: 10)
        engine.updateRegistry(for: high, capabilities: [.quotes], priority: 0)

        _ = try await engine.fetchQuote(symbol: "AAPL")
        #expect(await high.quoteCalls == 1)
        #expect(await low.quoteCalls == 0)
    }

    @Test("Retryable failure fails over to the next compatible provider")
    func retryableFailureFailsOver() async throws {
        let engine = makeEngine()
        let first = RoutingProvider(id: "first")
        let second = RoutingProvider(id: "second")
        await first.setFailure(.networkFailure("offline"))
        await engine.registerProvider(first)
        await engine.registerProvider(second)
        engine.updateRegistry(for: first, capabilities: [.quotes], priority: 0)
        engine.updateRegistry(for: second, capabilities: [.quotes], priority: 1)

        _ = try await engine.fetchQuote(symbol: "AAPL")
        #expect(await first.quoteCalls == 1)
        #expect(await second.quoteCalls == 1)
        #expect(engine.metrics(for: "first")?.selectedCount == 1)
        #expect(engine.metrics(for: "second")?.successfulFailoverCount == 1)
    }

    @Test("All retryable failures produce an aggregate error")
    func allFailuresAggregate() async {
        let engine = makeEngine()
        let first = RoutingProvider(id: "first")
        let second = RoutingProvider(id: "second")
        await first.setFailure(.networkFailure("offline"))
        await second.setFailure(.rateLimitExceeded("busy"))
        await engine.registerProvider(first)
        await engine.registerProvider(second)
        engine.updateRegistry(for: first, capabilities: [.quotes], priority: 0)
        engine.updateRegistry(for: second, capabilities: [.quotes], priority: 1)

        do {
            _ = try await engine.fetchQuote(symbol: "AAPL")
            Issue.record("Expected aggregate error")
        } catch let error as FinancialError {
            guard case .providerFailures(let capability, let failures) = error else { Issue.record("Wrong error: \(error)"); return }
            #expect(capability == "quotes")
            #expect(failures.count == 2)
        } catch { Issue.record("Unexpected error: \(error)") }
        #expect(engine.metrics(for: "second")?.finalFailureCount == 1)
    }

    @Test("Health is cached between selections")
    func healthIsCached() async throws {
        let engine = makeEngine()
        let provider = RoutingProvider(id: "cached")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes])

        _ = try await engine.fetchQuote(symbol: "AAPL")
        _ = try await engine.fetchQuote(symbol: "MSFT")
        #expect(await provider.healthCalls == 1)
    }

    @Test("Circuit-open provider is skipped")
    func circuitOpenProviderIsSkipped() async {
        let engine = makeEngine()
        let provider = RoutingProvider(id: "open")
        await provider.setFailure(.networkFailure("offline"))
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes])

        for index in 0..<5 {
            _ = try? await engine.fetchQuote(symbol: "AAPL-\(index)")
        }
        do {
            _ = try await engine.fetchQuote(symbol: "AAPL-final")
            Issue.record("Expected providerNotAvailable")
        } catch let error as FinancialError {
            guard case .providerNotAvailable = error else { Issue.record("Wrong error: \(error)"); return }
        } catch { Issue.record("Unexpected error: \(error)") }
        #expect(engine.metrics(for: "open")?.circuitOpenCount == 1)
    }

    @Test("Concurrent selections remain deterministic")
    func concurrentSelections() async throws {
        let engine = makeEngine()
        let provider = RoutingProvider(id: "concurrent")
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes])

        try await withThrowingTaskGroup(of: Quote.self) { group in
            for index in 0..<20 {
                group.addTask { try await engine.fetchQuote(symbol: "S\(index)") }
            }
            for try await quote in group { #expect(quote.price == 100) }
        }
        #expect(await provider.quoteCalls == 20)
    }

    @Test("Empty registry throws typed unavailability")
    func emptyRegistry() async {
        let engine = makeEngine()
        do {
            _ = try await engine.fetchNews()
            Issue.record("Expected providerNotAvailable")
        } catch let error as FinancialError {
            guard case .providerNotAvailable("news") = error else { Issue.record("Wrong error: \(error)"); return }
        } catch { Issue.record("Unexpected error: \(error)") }
    }

    @Test("Provider with multiple capabilities routes each supported request")
    func multipleCapabilities() async throws {
        let engine = makeEngine()
        let provider = RoutingProvider(id: "multi", capabilities: [.quotes, .ohlcv, .companyProfile])
        await engine.registerProvider(provider)
        engine.updateRegistry(for: provider, capabilities: [.quotes, .ohlcv, .companyProfile])

        _ = try await engine.fetchQuote(symbol: "AAPL")
        let profile = try await engine.fetchCompanyProfile(symbol: "AAPL")
        #expect(profile.name == "multi")
    }

    private func makeEngine() -> FinancialEngine {
        FinancialEngine(logger: Logger(configuration: .init(minimumLevel: .error)))
    }
}
