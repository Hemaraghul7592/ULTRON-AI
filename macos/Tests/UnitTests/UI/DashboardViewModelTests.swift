import Foundation
import Testing

@testable import ULTRON

private actor DashboardProvider: FinancialProvider {
    let providerID = "dashboard-test-provider"
    let providerName = "Dashboard Test Provider"
    let financialCapabilities: Set<FinancialCapability> = [.marketIndices, .news]
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []

    private let shouldFail: Bool
    private let delayNanoseconds: UInt64
    private(set) var activeRequests = 0
    private(set) var maximumConcurrentRequests = 0

    init(shouldFail: Bool = false, delayNanoseconds: UInt64 = 0) {
        self.shouldFail = shouldFail
        self.delayNanoseconds = delayNanoseconds
    }

    func initialize() async throws {}
    func healthCheck() async -> HealthStatus { .healthy }
    func shutdown() async {}

    func fetchQuote(symbol: String) async throws -> Quote {
        throw FinancialError.unsupportedCapability("quotes")
    }

    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] {
        throw FinancialError.unsupportedCapability("ohlcv")
    }

    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        throw FinancialError.unsupportedCapability("company_profile")
    }

    func fetchIndices() async throws -> [MarketIndex] {
        try await performRequest()
        if shouldFail { throw FinancialError.invalidData("test market failure") }
        return [MarketIndex(symbol: "TEST", name: "Test Market", value: 100)]
    }

    func fetchNews(symbols: [String]) async throws -> [NewsArticle] {
        try await performRequest()
        if shouldFail { throw FinancialError.invalidData("test news failure") }
        return [NewsArticle(title: "Injected article", source: "Test source", relatedSymbols: symbols)]
    }

    func execute(request: any Sendable) async throws -> any Sendable {
        throw FinancialError.unsupportedCapability("execute")
    }

    func getMaximumConcurrentRequests() -> Int { maximumConcurrentRequests }

    private func performRequest() async throws {
        activeRequests += 1
        maximumConcurrentRequests = max(maximumConcurrentRequests, activeRequests)
        defer { activeRequests -= 1 }
        if delayNanoseconds > 0 {
            try await Task.sleep(nanoseconds: delayNanoseconds)
        }
    }
}

@MainActor
@Suite struct DashboardViewModelTests {

    @Test("Initial loading state is idle")
    func loadingState() async {
        let viewModel = await makeViewModel().viewModel
        #expect(viewModel.loadingState == .idle)
    }

    @Test("Refresh publishes loading state before completion")
    func loadingStateDuringRefresh() async {
        let provider = DashboardProvider(delayNanoseconds: 50_000_000)
        let viewModel = await makeViewModel(provider: provider).viewModel
        let refreshTask = Task { await viewModel.refresh() }

        await Task.yield()
        #expect(viewModel.loadingState == .loading)
        await refreshTask.value
    }

    @Test("Refresh publishes loaded state and injected engine data")
    func successState() async {
        let provider = DashboardProvider()
        let (viewModel, portfolioEngine) = await makeViewModel(provider: provider)
        _ = portfolioEngine.createPortfolio(name: "Test", cash: 1_000)

        await viewModel.refresh()

        #expect(viewModel.loadingState == .loaded)
        #expect(viewModel.state.selectedPortfolioSummary?.totalValue == 1_000)
        #expect(viewModel.state.marketStatus == .available)
        #expect(viewModel.state.latestFinancialNews.count == 1)
    }

    @Test("Unexpected engine failure publishes a user-facing failed state")
    func failureState() async {
        let provider = DashboardProvider(shouldFail: true)
        let viewModel = await makeViewModel(provider: provider).viewModel

        await viewModel.refresh()

        if case .failed(let message) = viewModel.loadingState {
            #expect(message.contains("Dashboard could not be refreshed"))
        } else {
            Issue.record("Expected failed dashboard state")
        }
    }

    @Test("Empty portfolio, alerts, and news remain empty after refresh")
    func emptyState() async {
        let viewModel = await makeViewModel().viewModel

        await viewModel.refresh()

        #expect(viewModel.loadingState == .loaded)
        #expect(viewModel.state.selectedPortfolioSummary == nil)
        #expect(viewModel.state.activeAlerts.isEmpty)
        #expect(viewModel.state.latestFinancialNews.isEmpty)
        #expect(viewModel.state.aiDailyInsight != nil)
    }

    @Test("Initializer uses supplied engine dependencies")
    func dependencyInjection() async {
        let provider = DashboardProvider()
        let (viewModel, portfolioEngine) = await makeViewModel(provider: provider)
        let watchlist = portfolioEngine.createWatchlist(name: "Injected")
        try? portfolioEngine.addToWatchlist(watchlistID: watchlist.id, symbol: "TEST")

        await viewModel.refreshPortfolio()
        await viewModel.refreshNews()

        #expect(viewModel.state.watchlists.first?.name == "Injected")
        #expect(viewModel.state.latestFinancialNews.first?.title == "Injected article")
    }

    @Test("Refresh runs independent financial loads concurrently")
    func concurrentRefresh() async {
        let provider = DashboardProvider(delayNanoseconds: 50_000_000)
        let viewModel = await makeViewModel(provider: provider).viewModel

        await viewModel.refresh()

        #expect(await provider.getMaximumConcurrentRequests() >= 2)
    }

    private func makeViewModel(provider: DashboardProvider? = nil) async -> (viewModel: DashboardViewModel, portfolioEngine: PortfolioEngine) {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let portfolioEngine = PortfolioEngine(storage: InMemoryStorage(), logger: logger)
        let financialEngine = FinancialEngine(logger: logger)
        let alertEngine = AlertEngine(logger: logger)
        let visualizationEngine = VisualizationEngine(logger: logger)
        let advisorProvider = MockLLMProvider(response: "Injected daily insight")
        let advisorEngine = AIAdvisorEngine(primary: advisorProvider, fallback: advisorProvider, logger: logger)

        if let provider {
            await financialEngine.registerProvider(provider)
            financialEngine.updateRegistry(for: provider, capabilities: provider.financialCapabilities)
        }

        return (
            DashboardViewModel(
                portfolioEngine: portfolioEngine,
                financialEngine: financialEngine,
                alertEngine: alertEngine,
                visualizationEngine: visualizationEngine,
                advisorEngine: advisorEngine
            ),
            portfolioEngine
        )
    }
}
