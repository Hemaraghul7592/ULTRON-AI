import Foundation
import SwiftUI

public enum DashboardLoadingState: Equatable, Sendable {
    case idle
    case loading
    case loaded
    case failed(String)
}

public enum DashboardMarketStatus: String, Sendable {
    case available = "Available"
    case unavailable = "Unavailable"
}

public struct DashboardState: Sendable {
    public var portfolioSummaries: [PortfolioSummary] = []
    public var selectedPortfolioSummary: PortfolioSummary?
    public var watchlists: [Watchlist] = []
    public var marketStatus: DashboardMarketStatus = .unavailable
    public var activeAlerts: [Alert] = []
    public var latestFinancialNews: [NewsArticle] = []
    public var aiDailyInsight: AdvisorResponse?
    public var recentPortfolioPerformance: ChartData?
    public var portfolioAllocation: ChartData?
    public var lastUpdated: Date?

    public var portfolioTotalValue: Double? { selectedPortfolioSummary?.totalValue }
    public var todaysProfitLoss: Double? { selectedPortfolioSummary?.dayChange }

    public init(
        portfolioSummaries: [PortfolioSummary] = [],
        selectedPortfolioSummary: PortfolioSummary? = nil,
        watchlists: [Watchlist] = [],
        marketStatus: DashboardMarketStatus = .unavailable,
        activeAlerts: [Alert] = [],
        latestFinancialNews: [NewsArticle] = [],
        aiDailyInsight: AdvisorResponse? = nil,
        recentPortfolioPerformance: ChartData? = nil,
        portfolioAllocation: ChartData? = nil,
        lastUpdated: Date? = nil
    ) {
        self.portfolioSummaries = portfolioSummaries
        self.selectedPortfolioSummary = selectedPortfolioSummary
        self.watchlists = watchlists
        self.marketStatus = marketStatus
        self.activeAlerts = activeAlerts
        self.latestFinancialNews = latestFinancialNews
        self.aiDailyInsight = aiDailyInsight
        self.recentPortfolioPerformance = recentPortfolioPerformance
        self.portfolioAllocation = portfolioAllocation
        self.lastUpdated = lastUpdated
    }
}

/// Main-actor presentation state for the dashboard.
///
/// The view model only coordinates existing engines and exposes their models
/// to SwiftUI. Calculations remain in the domain engines.
@MainActor
public final class DashboardViewModel: ObservableObject {

    @Published public private(set) var loadingState: DashboardLoadingState = .idle
    @Published public private(set) var state = DashboardState()

    private let portfolioEngine: PortfolioEngine
    private let financialEngine: FinancialEngine
    private let alertEngine: AlertEngine
    private let visualizationEngine: VisualizationEngine
    private let advisorEngine: AIAdvisorEngine

    public init(
        portfolioEngine: PortfolioEngine,
        financialEngine: FinancialEngine,
        alertEngine: AlertEngine,
        visualizationEngine: VisualizationEngine,
        advisorEngine: AIAdvisorEngine,
        initialState: DashboardState = DashboardState(),
        initialLoadingState: DashboardLoadingState = .idle
    ) {
        self.portfolioEngine = portfolioEngine
        self.financialEngine = financialEngine
        self.alertEngine = alertEngine
        self.visualizationEngine = visualizationEngine
        self.advisorEngine = advisorEngine
        state = initialState
        loadingState = initialLoadingState
    }

    public func loadDashboard() async {
        await refresh()
    }

    public func refresh() async {
        loadingState = .loading

        do {
            let portfolioData = loadPortfolioData()
            async let marketStatus = loadMarketStatus()
            async let alerts = alertEngine.getActive()
            async let news = loadNews(symbols: portfolioData.symbols)

            let loadedMarketStatus = try await marketStatus
            let loadedAlerts = await alerts
            let loadedNews = try await news
            let insight = await loadAIInsight(
                summary: portfolioData.selectedSummary,
                news: loadedNews
            )

            state = DashboardState(
                portfolioSummaries: portfolioData.summaries,
                selectedPortfolioSummary: portfolioData.selectedSummary,
                watchlists: portfolioData.watchlists,
                marketStatus: loadedMarketStatus,
                activeAlerts: loadedAlerts,
                latestFinancialNews: loadedNews,
                aiDailyInsight: insight,
                recentPortfolioPerformance: portfolioData.performance,
                portfolioAllocation: portfolioData.allocation,
                lastUpdated: Date()
            )
            loadingState = .loaded
        } catch {
            loadingState = .failed(userMessage(for: error))
        }
    }

    public func refreshPortfolio() async {
        let portfolioData = loadPortfolioData()
        state.portfolioSummaries = portfolioData.summaries
        state.selectedPortfolioSummary = portfolioData.selectedSummary
        state.watchlists = portfolioData.watchlists
        state.recentPortfolioPerformance = portfolioData.performance
        state.portfolioAllocation = portfolioData.allocation
    }

    public func refreshAlerts() async {
        state.activeAlerts = await alertEngine.getActive()
    }

    public func refreshNews() async {
        do {
            state.latestFinancialNews = try await loadNews(symbols: state.watchlists.flatMap { $0.symbols.map(\.symbol) })
        } catch {
            loadingState = .failed(userMessage(for: error))
        }
    }

    public func refreshAIInsight() async {
        state.aiDailyInsight = await loadAIInsight(
            summary: state.selectedPortfolioSummary,
            news: state.latestFinancialNews
        )
    }

    private func loadPortfolioData() -> PortfolioData {
        let portfolios = portfolioEngine.getAllPortfolios()
        let summaries = portfolios.compactMap { portfolioEngine.summary(for: $0.id) }
        let selectedPortfolio = portfolios.first
        let watchlists = portfolioEngine.getAllWatchlists()
        let symbols = watchlists.flatMap { $0.symbols.map(\.symbol) }
        let performance = visualizationEngine.portfolioValueChart([])
        let allocation = selectedPortfolio.map { portfolio in
            visualizationEngine.assetAllocationChart(
                portfolio.holdings.compactMap { holding in
                    guard let value = holding.currentValue else { return nil }
                    return (symbol: holding.symbol, value: value)
                }
            )
        }

        return PortfolioData(
            summaries: summaries,
            selectedSummary: summaries.first,
            watchlists: watchlists,
            symbols: symbols,
            performance: performance.points.isEmpty ? nil : performance,
            allocation: allocation?.segments.isEmpty == false ? allocation : nil
        )
    }

    private func loadMarketStatus() async throws -> DashboardMarketStatus {
        do {
            return try await financialEngine.fetchIndices().isEmpty ? .unavailable : .available
        } catch let error as FinancialError {
            switch error {
            case .providerNotAvailable, .symbolNotFound, .unsupportedCapability:
                return .unavailable
            default:
                throw error
            }
        }
    }

    private func loadNews(symbols: [String]) async throws -> [NewsArticle] {
        do {
            return try await financialEngine.fetchNews(symbols: symbols)
        } catch let error as FinancialError {
            switch error {
            case .providerNotAvailable, .symbolNotFound, .unsupportedCapability:
                return []
            default:
                throw error
            }
        }
    }

    private func loadAIInsight(summary: PortfolioSummary?, news: [NewsArticle]) async -> AdvisorResponse? {
        let response = await advisorEngine.ask(
            AdvisorRequest(
                question: "Provide a concise daily financial insight.",
                portfolioSnapshot: summary,
                news: news
            )
        )
        return response.provider == "none" ? nil : response
    }

    private func userMessage(for error: Error) -> String {
        "Dashboard could not be refreshed. Please try again. (\(error))"
    }
}

private struct PortfolioData: Sendable {
    let summaries: [PortfolioSummary]
    let selectedSummary: PortfolioSummary?
    let watchlists: [Watchlist]
    let symbols: [String]
    let performance: ChartData?
    let allocation: ChartData?
}

#if DEBUG
enum DashboardPreviewFactory {
    enum PreviewState {
        case loading
        case loaded
        case empty
        case failed(String)
    }

    @MainActor
    static func make(state: PreviewState) -> DashboardViewModel {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let loadingState: DashboardLoadingState
        let dashboardState: DashboardState

        switch state {
        case .loading:
            loadingState = .loading
            dashboardState = DashboardState()
        case .loaded:
            loadingState = .loaded
            dashboardState = DashboardState(lastUpdated: Date())
        case .empty:
            loadingState = .loaded
            dashboardState = DashboardState()
        case .failed(let message):
            loadingState = .failed(message)
            dashboardState = DashboardState()
        }

        return DashboardViewModel(
            portfolioEngine: PortfolioEngine(storage: InMemoryStorage(), logger: logger),
            financialEngine: FinancialEngine(logger: logger),
            alertEngine: AlertEngine(logger: logger),
            visualizationEngine: VisualizationEngine(logger: logger),
            advisorEngine: AIAdvisorEngine(
                primary: MockLLMProvider(),
                fallback: MockLLMProvider(),
                logger: logger
            ),
            initialState: dashboardState,
            initialLoadingState: loadingState
        )
    }
}
#endif
