import Foundation
import Testing

@testable import ULTRON

private actor ResearchProvider: FinancialProvider {
    let providerID = "research-test"
    let providerName = "Research Test"
    let financialCapabilities: Set<FinancialCapability> = [.quotes, .ohlcv, .companyProfile, .news]
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []
    private let failing: Bool
    private let delay: UInt64
    private var active = 0
    private var maximum = 0

    init(failing: Bool = false, delay: UInt64 = 0) { self.failing = failing; self.delay = delay }
    func initialize() async throws {}
    func healthCheck() async -> HealthStatus { .healthy }
    func shutdown() async {}
    func fetchQuote(symbol: String) async throws -> Quote { try await request(); if failing { throw FinancialError.invalidData("quote") }; return Quote(symbol: symbol, price: 100, change: 1, changePercent: 1, volume: 1000, timestamp: Date()) }
    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { try await request(); if failing { throw FinancialError.invalidData("history") }; return (0..<35).map { i in let close = 100 + Double(i); return OHLCV(symbol: symbol, open: close - 1, high: close + 2, low: close - 2, close: close, volume: 1000, timestamp: Date(timeIntervalSince1970: Double(i) * 86400)) } }
    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile { try await request(); if failing { throw FinancialError.invalidData("profile") }; return CompanyProfile(symbol: symbol, name: "Research Company", sector: "Technology", industry: "Software") }
    func fetchIndices() async throws -> [MarketIndex] { [] }
    func fetchNews(symbols: [String]) async throws -> [NewsArticle] { try await request(); if failing { throw FinancialError.invalidData("news") }; return [NewsArticle(title: "Research headline", source: "Research source", relatedSymbols: symbols)] }
    func execute(request: any Sendable) async throws -> any Sendable { "ok" }
    func maximumConcurrency() -> Int { maximum }
    private func request() async throws { active += 1; maximum = max(maximum, active); defer { active -= 1 }; if delay > 0 { try await Task.sleep(nanoseconds: delay) } }
}

@MainActor
@Suite struct ResearchWorkspaceViewModelTests {
    @Test("Empty search publishes empty state")
    func emptySearch() async { let vm = await make().viewModel; await vm.search(); #expect(vm.loadingState == .empty) }

    @Test("Search loads company research")
    func search() async { let setup = await make(); setup.viewModel.searchQuery = "TEST"; await setup.viewModel.search(); #expect(setup.viewModel.loadingState == .loaded); #expect(setup.viewModel.company?.name == "Research Company"); #expect(setup.viewModel.quote?.price == 100) }

    @Test("Provider failure publishes error")
    func failure() async { let vm = await make(provider: ResearchProvider(failing: true)).viewModel; await vm.selectSymbol("TEST"); if case .failed = vm.loadingState { #expect(vm.loadingState != .loaded) } else { Issue.record("Expected research error") } }

    @Test("Concurrent research loads are concurrent")
    func concurrentLoading() async { let provider = ResearchProvider(delay: 40_000_000); let setup = await make(provider: provider); await setup.viewModel.selectSymbol("TEST"); #expect(await provider.maximumConcurrency() >= 2) }

    @Test("Refresh methods delegate to injected services")
    func refreshes() async { let vm = await make().viewModel; await vm.selectSymbol("TEST"); await vm.refreshNews(); await vm.refreshTechnicalAnalysis(); await vm.refreshFundamentalAnalysis(); await vm.refreshAIAnalysis(); #expect(vm.news.count == 1); #expect(vm.technical.rsi != nil); #expect(vm.fundamental.score == nil); #expect(vm.aiResearch != nil) }

    @Test("Notes and export remain local to the ViewModel")
    func notesAndExport() async { let vm = await make().viewModel; await vm.selectSymbol("TEST"); vm.notes = "Local thesis"; vm.saveNotes(); #expect(vm.exportMarkdown().contains("Local thesis")); #expect(vm.exportJSON() != nil) }

    private func make(provider: ResearchProvider? = nil) async -> (viewModel: ResearchWorkspaceViewModel, provider: ResearchProvider) {
        let logger = Logger(configuration: .init(minimumLevel: .error)); let financial = FinancialEngine(logger: logger); let selected = provider ?? ResearchProvider(); await financial.registerProvider(selected); financial.updateRegistry(for: selected, capabilities: selected.financialCapabilities); let ai = MockLLMProvider(response: "Research analysis")
        return (ResearchWorkspaceViewModel(financialEngine: financial, fundamentalEngine: FundamentalAnalysisEngine(), technicalEngine: TechnicalAnalysisEngine(), visualizationEngine: VisualizationEngine(logger: logger), advisorEngine: AIAdvisorEngine(primary: ai, fallback: ai, logger: logger), portfolioEngine: PortfolioEngine(storage: InMemoryStorage(), logger: logger)), selected)
    }
}
