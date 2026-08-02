import Foundation
import Testing

@testable import ULTRON

private actor MarketWorkspaceProvider: FinancialProvider {
    let providerID = "market-workspace-test"
    let providerName = "Market Workspace Test"
    let financialCapabilities: Set<FinancialCapability> = [.quotes, .ohlcv, .companyProfile, .news, .marketIndices]
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []

    private let shouldFail: Bool
    private let delayNanoseconds: UInt64
    private var activeRequests = 0
    private var maximumConcurrentRequests = 0

    init(shouldFail: Bool = false, delayNanoseconds: UInt64 = 0) {
        self.shouldFail = shouldFail
        self.delayNanoseconds = delayNanoseconds
    }

    func initialize() async throws {}
    func healthCheck() async -> HealthStatus { .healthy }
    func shutdown() async {}

    func fetchQuote(symbol: String) async throws -> Quote {
        try await request()
        if shouldFail { throw FinancialError.invalidData("quote failure") }
        return Quote(symbol: symbol, price: 150, change: 2, changePercent: 1.3, volume: 10_000, timestamp: Date())
    }

    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        try await request()
        if shouldFail { throw FinancialError.invalidData("history failure") }
        return (0..<40).map { index in
            let close = 100 + Double(index)
            return OHLCV(symbol: symbol, open: close - 1, high: close + 2, low: close - 2, close: close, volume: 1_000, timestamp: Date(timeIntervalSince1970: Double(index) * 86_400))
        }
    }

    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        try await request()
        if shouldFail { throw FinancialError.invalidData("profile failure") }
        return CompanyProfile(symbol: symbol, name: "Test Company", exchange: "TEST", sector: "Technology", industry: "Software", marketCap: 1_000_000)
    }

    func fetchIndices() async throws -> [MarketIndex] {
        try await request()
        if shouldFail { throw FinancialError.invalidData("indices failure") }
        return [MarketIndex(symbol: "TEST", name: "Test Index", value: 100, changePercent: 1)]
    }

    func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        try await request()
        if shouldFail { throw FinancialError.invalidData("news failure") }
        return [NewsArticle(title: "Test headline", summary: "Test summary", source: "Test source", relatedSymbols: symbols)]
    }

    func execute(request: any Sendable) async throws -> any Sendable { "ok" }

    func maximumConcurrency() -> Int { maximumConcurrentRequests }

    private func request() async throws {
        activeRequests += 1
        maximumConcurrentRequests = max(maximumConcurrentRequests, activeRequests)
        defer { activeRequests -= 1 }
        if delayNanoseconds > 0 { try await Task.sleep(nanoseconds: delayNanoseconds) }
    }
}

@MainActor
@Suite struct MarketWorkspaceViewModelTests {
    @Test("Initial loading state is idle")
    func loadingState() async {
        let viewModel = await makeViewModel().viewModel
        #expect(viewModel.loadingState == .idle)
    }

    @Test("Empty search produces empty state")
    func emptySearch() async {
        let viewModel = await makeViewModel().viewModel
        await viewModel.search()
        #expect(viewModel.loadingState == .empty)
    }

    @Test("Successful symbol search loads quote and company profile")
    func successfulQuoteLoad() async {
        let setup = await makeViewModel()
        setup.viewModel.searchQuery = "TEST"
        await setup.viewModel.search()

        #expect(setup.viewModel.loadingState == .loaded)
        #expect(setup.viewModel.state.quote?.price == 150)
        #expect(setup.viewModel.state.company?.name == "Test Company")
        #expect(setup.viewModel.state.news.count == 1)
    }

    @Test("Provider failure produces error state")
    func engineFailure() async {
        let viewModel = await makeViewModel(provider: MarketWorkspaceProvider(shouldFail: true)).viewModel
        await viewModel.selectSymbol("TEST")

        if case .failed = viewModel.loadingState {
            #expect(viewModel.loadingState != .loaded)
        } else {
            Issue.record("Expected market workspace failure")
        }
    }

    @Test("Initial loads run concurrently")
    func concurrentLoading() async {
        let provider = MarketWorkspaceProvider(delayNanoseconds: 40_000_000)
        let setup = await makeViewModel(provider: provider)
        await setup.viewModel.selectSymbol("TEST")

        #expect(await provider.maximumConcurrency() >= 2)
    }

    @Test("News refresh replaces news state")
    func newsRefresh() async {
        let setup = await makeViewModel()
        await setup.viewModel.selectSymbol("TEST")
        await setup.viewModel.refreshNews()

        #expect(setup.viewModel.state.news.first?.title == "Test headline")
    }

    @Test("AI refresh uses injected advisor")
    func aiRefresh() async {
        let setup = await makeViewModel()
        await setup.viewModel.selectSymbol("TEST")
        await setup.viewModel.refreshAIAnalysis()

        #expect(setup.viewModel.state.aiAnalysis?.summary == "Injected analysis")
    }

    @Test("Technical refresh uses TechnicalAnalysisEngine")
    func technicalRefresh() async {
        let setup = await makeViewModel()
        await setup.viewModel.selectSymbol("TEST")
        await setup.viewModel.refreshTechnicalAnalysis()

        #expect(setup.viewModel.state.technical.rsi != nil)
    }

    @Test("Fundamental refresh preserves empty state without statements")
    func fundamentalRefresh() async {
        let setup = await makeViewModel()
        await setup.viewModel.selectSymbol("TEST")
        await setup.viewModel.refreshFundamentalAnalysis()

        #expect(setup.viewModel.state.fundamental.score == nil)
        #expect(setup.viewModel.state.fundamental.valuation == nil)
    }

    private func makeViewModel(provider: MarketWorkspaceProvider? = nil) async -> (viewModel: MarketWorkspaceViewModel, provider: MarketWorkspaceProvider) {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let financialEngine = FinancialEngine(logger: logger)
        let selectedProvider = provider ?? MarketWorkspaceProvider()
        await financialEngine.registerProvider(selectedProvider)
        financialEngine.updateRegistry(for: selectedProvider, capabilities: selectedProvider.financialCapabilities)
        let advisor = MockLLMProvider(response: "Injected analysis")
        let viewModel = MarketWorkspaceViewModel(
            financialEngine: financialEngine,
            technicalEngine: TechnicalAnalysisEngine(),
            fundamentalEngine: FundamentalAnalysisEngine(),
            visualizationEngine: VisualizationEngine(logger: logger),
            advisorEngine: AIAdvisorEngine(primary: advisor, fallback: advisor, logger: logger)
        )
        return (viewModel, selectedProvider)
    }
}
