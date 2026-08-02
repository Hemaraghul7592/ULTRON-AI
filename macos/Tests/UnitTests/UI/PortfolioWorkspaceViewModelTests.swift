import Foundation
import Testing

@testable import ULTRON

private actor PortfolioWorkspaceProvider: FinancialProvider {
    let providerID = "portfolio-workspace-test"
    let providerName = "Portfolio Workspace Test"
    let financialCapabilities: Set<FinancialCapability> = [.quotes, .companyProfile]
    let category: ServiceCategory = .custom
    let capabilities: Set<ServiceCapability> = []

    func initialize() async throws {}
    func healthCheck() async -> HealthStatus { .healthy }
    func shutdown() async {}
    func fetchQuote(symbol: String) async throws -> Quote {
        Quote(symbol: symbol, price: 110, change: 2, changePercent: 1.8, volume: 1_000, timestamp: Date())
    }
    func fetchOHLCV(symbol: String, range: OHLCVRange) async throws -> [OHLCV] { [] }
    func fetchCompanyProfile(symbol: String) async throws -> CompanyProfile {
        CompanyProfile(symbol: symbol, name: "Test Company", sector: "Technology")
    }
    func fetchIndices() async throws -> [MarketIndex] { [] }
    func fetchNews(symbols: [String]) async throws -> [NewsArticle] { [] }
    func execute(request: any Sendable) async throws -> any Sendable { "ok" }
}

@MainActor
@Suite struct PortfolioWorkspaceViewModelTests {
    @Test("Empty portfolio produces empty workspace state")
    func emptyWorkspace() async {
        let viewModel = await makeViewModel().viewModel

        await viewModel.refresh()

        #expect(viewModel.loadingState == .empty)
        #expect(viewModel.selectedPortfolio == nil)
        #expect(viewModel.displayedHoldings.isEmpty)
    }

    @Test("Workspace loads injected portfolio and market data")
    func loadedWorkspace() async throws {
        let setup = await makeViewModel()
        let portfolio = setup.portfolioEngine.createPortfolio(name: "Primary", cash: 1_000)
        try setup.portfolioEngine.addTransaction(
            to: portfolio.id,
            Transaction(type: .buy, symbol: "TEST", quantity: 2, price: 100)
        )

        await setup.viewModel.refresh()

        #expect(setup.viewModel.loadingState == .loaded)
        #expect(setup.viewModel.selectedPortfolio?.name == "Primary")
        #expect(setup.viewModel.holdings.count == 1)
        #expect(setup.viewModel.holdings.first?.companyName == "Test Company")
        #expect(setup.viewModel.holdings.first?.currentPrice == 110)
    }

    @Test("Search and filter update displayed holdings")
    func holdingFiltering() async throws {
        let setup = await makeViewModel()
        let portfolio = setup.portfolioEngine.createPortfolio(name: "Primary", cash: 1_000)
        try setup.portfolioEngine.addTransaction(to: portfolio.id, Transaction(type: .buy, symbol: "TEST", quantity: 2, price: 100))
        await setup.viewModel.refresh()

        setup.viewModel.searchText = "missing"
        #expect(setup.viewModel.displayedHoldings.isEmpty)

        setup.viewModel.searchText = "test"
        #expect(setup.viewModel.displayedHoldings.count == 1)
    }

    @Test("Portfolio selection is driven by the injected engine")
    func portfolioSelection() async throws {
        let setup = await makeViewModel()
        let first = setup.portfolioEngine.createPortfolio(name: "First", cash: 100)
        _ = setup.portfolioEngine.createPortfolio(name: "Second", cash: 200)
        await setup.viewModel.refresh()
        await setup.viewModel.selectPortfolio(id: first.id)

        #expect(setup.viewModel.selectedPortfolio?.id == first.id)
        #expect(setup.viewModel.selectedPortfolioID == first.id)
    }

    private func makeViewModel() async -> (viewModel: PortfolioWorkspaceViewModel, portfolioEngine: PortfolioEngine) {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let portfolioEngine = PortfolioEngine(storage: InMemoryStorage(), logger: logger)
        let financialEngine = FinancialEngine(logger: logger)
        let provider = PortfolioWorkspaceProvider()
        await financialEngine.registerProvider(provider)
        financialEngine.updateRegistry(for: provider, capabilities: provider.financialCapabilities)
        let aiProvider = MockLLMProvider(response: "Portfolio review")
        let viewModel = PortfolioWorkspaceViewModel(
            portfolioEngine: portfolioEngine,
            financialEngine: financialEngine,
            visualizationEngine: VisualizationEngine(logger: logger),
            advisorEngine: AIAdvisorEngine(primary: aiProvider, fallback: aiProvider, logger: logger)
        )
        return (viewModel, portfolioEngine)
    }
}
