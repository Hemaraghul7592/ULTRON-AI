import Foundation
import SwiftUI

public enum PortfolioWorkspaceLoadingState: Equatable, Sendable {
    case idle
    case loading
    case refreshing
    case loaded
    case empty
    case failed(String)
}

public enum PortfolioHoldingSort: String, CaseIterable, Sendable {
    case symbol = "Symbol"
    case marketValue = "Market Value"
    case totalReturn = "Total Return"
    case todaysChange = "Today's Change"
}

public enum PortfolioHoldingFilter: String, CaseIterable, Sendable {
    case all = "All"
    case winners = "Winners"
    case losers = "Losers"
}

public struct PortfolioHoldingRow: Identifiable, Sendable {
    public let holding: Holding
    public let quote: Quote?
    public let company: CompanyProfile?
    public let weight: Double?

    public var id: String { holding.id }
    public var symbol: String { holding.symbol }
    public var companyName: String { company?.name ?? "Unavailable" }
    public var quantity: Double { holding.quantity }
    public var averagePrice: Double { holding.averagePrice }
    public var currentPrice: Double? { holding.currentPrice ?? quote?.price }
    public var marketValue: Double? { holding.currentValue ?? currentPrice.map { holding.quantity * $0 } }
    public var todaysChange: Double? { quote?.change }
    public var todaysChangePercent: Double? { quote?.changePercent }
    public var totalReturn: Double? { holding.unrealizedPLPercent }
    public var currency: String { holding.currency }

    public init(holding: Holding, quote: Quote?, company: CompanyProfile?, weight: Double?) {
        self.holding = holding
        self.quote = quote
        self.company = company
        self.weight = weight
    }
}

public struct PortfolioAnalytics: Sendable {
    public let diversificationScore: Double?
    public let largestHolding: String?
    public let sectorAllocationAvailable: Bool
    public let riskEstimate: Double?
    public let annualizedReturn: Double?
    public let maxDrawdown: Double?
    public let cagr: Double?

    public init(
        diversificationScore: Double? = nil,
        largestHolding: String? = nil,
        sectorAllocationAvailable: Bool = false,
        riskEstimate: Double? = nil,
        annualizedReturn: Double? = nil,
        maxDrawdown: Double? = nil,
        cagr: Double? = nil
    ) {
        self.diversificationScore = diversificationScore
        self.largestHolding = largestHolding
        self.sectorAllocationAvailable = sectorAllocationAvailable
        self.riskEstimate = riskEstimate
        self.annualizedReturn = annualizedReturn
        self.maxDrawdown = maxDrawdown
        self.cagr = cagr
    }
}

@MainActor
public final class PortfolioWorkspaceViewModel: ObservableObject {
    @Published public private(set) var loadingState: PortfolioWorkspaceLoadingState = .idle
    @Published public private(set) var portfolios: [Portfolio] = []
    @Published public private(set) var watchlists: [Watchlist] = []
    @Published public private(set) var selectedPortfolio: Portfolio?
    @Published public private(set) var summary: PortfolioSummary?
    @Published public private(set) var holdings: [PortfolioHoldingRow] = []
    @Published public private(set) var transactions: [Transaction] = []
    @Published public private(set) var allocationChart: ChartData?
    @Published public private(set) var performanceChart: ChartData?
    @Published public private(set) var aiReview: AdvisorResponse?
    @Published public private(set) var analytics = PortfolioAnalytics()
    @Published public private(set) var selectedPortfolioID: String?
    @Published public private(set) var selectedHoldingID: String?
    @Published public private(set) var lastUpdated: Date?

    @Published public var searchText = "" {
        didSet { applyHoldingFilters() }
    }
    @Published public var sort: PortfolioHoldingSort = .symbol {
        didSet { applyHoldingFilters() }
    }
    @Published public var filter: PortfolioHoldingFilter = .all {
        didSet { applyHoldingFilters() }
    }
    @Published public private(set) var displayedHoldings: [PortfolioHoldingRow] = []

    private let portfolioEngine: PortfolioEngine
    private let financialEngine: FinancialEngine
    private let visualizationEngine: VisualizationEngine
    private let advisorEngine: AIAdvisorEngine

    public init(
        portfolioEngine: PortfolioEngine,
        financialEngine: FinancialEngine,
        visualizationEngine: VisualizationEngine,
        advisorEngine: AIAdvisorEngine,
        initialLoadingState: PortfolioWorkspaceLoadingState = .idle
    ) {
        self.portfolioEngine = portfolioEngine
        self.financialEngine = financialEngine
        self.visualizationEngine = visualizationEngine
        self.advisorEngine = advisorEngine
        loadingState = initialLoadingState
    }

    public func loadWorkspace() async {
        await refresh()
    }

    public func refresh() async {
        loadingState = portfolios.isEmpty ? .loading : .refreshing
        do {
            portfolios = portfolioEngine.getAllPortfolios()
            watchlists = portfolioEngine.getAllWatchlists()

            guard !portfolios.isEmpty else {
                clearSelectedPortfolio()
                loadingState = .empty
                return
            }

            let targetID = selectedPortfolioID.flatMap { id in
                portfolios.contains { $0.id == id } ? id : nil
            } ?? portfolios[0].id
            selectedPortfolioID = targetID
            try await loadPortfolio(id: targetID)
            loadingState = .loaded
            lastUpdated = Date()
        } catch {
            loadingState = .failed(userMessage(for: error))
        }
    }

    public func selectPortfolio(id: String) async {
        guard portfolios.contains(where: { $0.id == id }) else { return }
        selectedPortfolioID = id
        loadingState = .refreshing
        do {
            try await loadPortfolio(id: id)
            loadingState = .loaded
            lastUpdated = Date()
        } catch {
            loadingState = .failed(userMessage(for: error))
        }
    }

    public func selectHolding(id: String?) {
        selectedHoldingID = id
    }

    public func refreshAIReview() async {
        aiReview = await loadAIReview()
    }

    private func loadPortfolio(id: String) async throws {
        guard let portfolio = portfolioEngine.getPortfolio(id: id) else {
            throw PortfolioError.notFound(id)
        }

        selectedPortfolio = portfolio
        summary = portfolioEngine.summary(for: id)
        transactions = portfolio.transactions
        let marketData = await loadMarketData(for: portfolio.holdings)

        let quotes = marketData.reduce(into: [String: Double]()) { result, item in
            if let price = item.quote?.price { result[item.holding.symbol] = price }
        }
        if !quotes.isEmpty {
            portfolioEngine.updatePrices(quotes: quotes)
        }

        let refreshedPortfolio = portfolioEngine.getPortfolio(id: id) ?? portfolio
        selectedPortfolio = refreshedPortfolio
        summary = portfolioEngine.summary(for: id)
        transactions = refreshedPortfolio.transactions
        holdings = buildRows(for: refreshedPortfolio, marketData: marketData)
        displayedHoldings = filteredAndSorted(holdings)
        allocationChart = buildAllocationChart(from: holdings)
        performanceChart = emptyPerformanceChart()
        analytics = buildAnalytics(for: refreshedPortfolio, rows: holdings, summary: summary)
        aiReview = await loadAIReview()
    }

    private func loadMarketData(for holdings: [Holding]) async -> [HoldingMarketData] {
        await withTaskGroup(of: HoldingMarketData.self, returning: [HoldingMarketData].self) { group in
            for holding in holdings {
                group.addTask { [financialEngine] in
                    async let quote = try? financialEngine.fetchQuote(symbol: holding.symbol)
                    async let company = try? financialEngine.fetchCompanyProfile(symbol: holding.symbol)
                    return HoldingMarketData(
                        holding: holding,
                        quote: await quote,
                        company: await company
                    )
                }
            }

            var result: [HoldingMarketData] = []
            for await item in group { result.append(item) }
            return result
        }
    }

    private func buildRows(for portfolio: Portfolio, marketData: [HoldingMarketData]) -> [PortfolioHoldingRow] {
        let totalValue = portfolio.totalValue
        return portfolio.holdings.map { holding in
            let data = marketData.first { $0.holding.id == holding.id }
            let weight = holding.currentValue.map {
                PortfolioCalculator.allocationPercent(holdingValue: $0, totalValue: totalValue)
            }
            return PortfolioHoldingRow(
                holding: holding,
                quote: data?.quote,
                company: data?.company,
                weight: weight
            )
        }
    }

    private func buildAllocationChart(from rows: [PortfolioHoldingRow]) -> ChartData? {
        let values = rows.compactMap { row in
            row.marketValue.map { (symbol: row.symbol, value: $0) }
        }
        guard !values.isEmpty else { return nil }
        let chart = visualizationEngine.assetAllocationChart(values)
        return chart.segments.isEmpty ? nil : chart
    }

    private func emptyPerformanceChart() -> ChartData? {
        let chart = visualizationEngine.portfolioValueChart([])
        return chart.points.isEmpty ? nil : chart
    }

    private func buildAnalytics(for portfolio: Portfolio, rows: [PortfolioHoldingRow], summary: PortfolioSummary?) -> PortfolioAnalytics {
        let values = rows.compactMap { row in
            row.marketValue.map { (symbol: row.symbol, value: $0) }
        }
        let years = max(Date().timeIntervalSince(portfolio.createdAt) / 31_557_600, 0)
        return PortfolioAnalytics(
            diversificationScore: values.isEmpty ? nil : PortfolioCalculator.diversificationScore(holdings: values),
            largestHolding: summary?.topHolding,
            sectorAllocationAvailable: rows.contains { $0.company?.sector.isEmpty == false },
            riskEstimate: nil,
            annualizedReturn: summary.flatMap {
                PortfolioCalculator.annualizedReturn(
                    totalReturn: $0.totalReturn,
                    totalInvested: $0.totalInvested,
                    years: years
                )
            },
            maxDrawdown: nil,
            cagr: nil
        )
    }

    private func loadAIReview() async -> AdvisorResponse? {
        guard let summary else { return nil }
        let response = await advisorEngine.ask(
            AdvisorRequest(
                question: "Review this portfolio. Explain strengths, weaknesses, suggestions, risk observations, and diversification recommendations.",
                portfolioSnapshot: summary
            )
        )
        return response.provider == "none" ? nil : response
    }

    private func applyHoldingFilters() {
        displayedHoldings = filteredAndSorted(holdings)
    }

    private func filteredAndSorted(_ rows: [PortfolioHoldingRow]) -> [PortfolioHoldingRow] {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        let filtered = rows.filter { row in
            let matchesSearch = query.isEmpty || row.symbol.lowercased().contains(query) || row.companyName.lowercased().contains(query)
            let matchesFilter: Bool
            switch filter {
            case .all: matchesFilter = true
            case .winners: matchesFilter = (row.totalReturn ?? 0) > 0
            case .losers: matchesFilter = (row.totalReturn ?? 0) < 0
            }
            return matchesSearch && matchesFilter
        }

        switch sort {
        case .symbol:
            return filtered.sorted { $0.symbol < $1.symbol }
        case .marketValue:
            return filtered.sorted { ($0.marketValue ?? 0) > ($1.marketValue ?? 0) }
        case .totalReturn:
            return filtered.sorted { ($0.totalReturn ?? 0) > ($1.totalReturn ?? 0) }
        case .todaysChange:
            return filtered.sorted { ($0.todaysChangePercent ?? 0) > ($1.todaysChangePercent ?? 0) }
        }
    }

    private func clearSelectedPortfolio() {
        selectedPortfolioID = nil
        selectedPortfolio = nil
        summary = nil
        holdings = []
        displayedHoldings = []
        transactions = []
        allocationChart = nil
        performanceChart = nil
        aiReview = nil
        analytics = PortfolioAnalytics()
        lastUpdated = nil
    }

    private func userMessage(for error: Error) -> String {
        "Portfolio could not be refreshed. Please try again. (\(error))"
    }
}

private struct HoldingMarketData: Sendable {
    let holding: Holding
    let quote: Quote?
    let company: CompanyProfile?
}
