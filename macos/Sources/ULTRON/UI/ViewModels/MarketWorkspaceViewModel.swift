import Foundation
import SwiftUI

public enum MarketWorkspaceLoadingState: Equatable, Sendable {
    case idle
    case loading
    case loaded
    case refreshing
    case empty
    case failed(String)
}

public enum MarketChartRange: String, CaseIterable, Sendable {
    case intraday = "Intraday"
    case oneWeek = "1 Week"
    case oneMonth = "1 Month"
    case threeMonths = "3 Months"
    case sixMonths = "6 Months"
    case oneYear = "1 Year"
    case fiveYears = "5 Years"

    var sourceRange: OHLCVRange? {
        switch self {
        case .intraday: .oneHour
        case .oneWeek: .oneWeek
        case .oneMonth: .oneMonth
        case .threeMonths, .sixMonths, .oneYear, .fiveYears: nil
        }
    }
}

public struct MarketTechnicalState: Sendable {
    public let rsi: RSIRresult?
    public let macd: MACDResult?
    public let movingAverage: EMA?
    public let bollingerBands: BollingerBands?
    public let signal: TASignal?
    public let patterns: [DetectedPattern]

    public init(
        rsi: RSIRresult? = nil,
        macd: MACDResult? = nil,
        movingAverage: EMA? = nil,
        bollingerBands: BollingerBands? = nil,
        signal: TASignal? = nil,
        patterns: [DetectedPattern] = []
    ) {
        self.rsi = rsi
        self.macd = macd
        self.movingAverage = movingAverage
        self.bollingerBands = bollingerBands
        self.signal = signal
        self.patterns = patterns
    }
}

public struct MarketFundamentalState: Sendable {
    public let valuation: RatioReport?
    public let intrinsicValue: ValuationResult?
    public let score: FundamentalScore?
    public let profitability: ProfitabilityReport?
    public let cashFlow: CashFlowStatement?

    public init(
        valuation: RatioReport? = nil,
        intrinsicValue: ValuationResult? = nil,
        score: FundamentalScore? = nil,
        profitability: ProfitabilityReport? = nil,
        cashFlow: CashFlowStatement? = nil
    ) {
        self.valuation = valuation
        self.intrinsicValue = intrinsicValue
        self.score = score
        self.profitability = profitability
        self.cashFlow = cashFlow
    }
}

public struct MarketWorkspaceState: Sendable {
    public var symbol: String?
    public var quote: Quote?
    public var company: CompanyProfile?
    public var history: [OHLCV]
    public var priceChart: ChartData?
    public var marketIndices: [MarketIndex]
    public var news: [NewsArticle]
    public var technical: MarketTechnicalState
    public var fundamental: MarketFundamentalState
    public var aiAnalysis: AdvisorResponse?
    public var selectedRange: MarketChartRange
    public var lastUpdated: Date?

    public init(
        symbol: String? = nil,
        quote: Quote? = nil,
        company: CompanyProfile? = nil,
        history: [OHLCV] = [],
        priceChart: ChartData? = nil,
        marketIndices: [MarketIndex] = [],
        news: [NewsArticle] = [],
        technical: MarketTechnicalState = MarketTechnicalState(),
        fundamental: MarketFundamentalState = MarketFundamentalState(),
        aiAnalysis: AdvisorResponse? = nil,
        selectedRange: MarketChartRange = .oneMonth,
        lastUpdated: Date? = nil
    ) {
        self.symbol = symbol
        self.quote = quote
        self.company = company
        self.history = history
        self.priceChart = priceChart
        self.marketIndices = marketIndices
        self.news = news
        self.technical = technical
        self.fundamental = fundamental
        self.aiAnalysis = aiAnalysis
        self.selectedRange = selectedRange
        self.lastUpdated = lastUpdated
    }
}

@MainActor
public final class MarketWorkspaceViewModel: ObservableObject {
    @Published public private(set) var loadingState: MarketWorkspaceLoadingState = .idle
    @Published public private(set) var state = MarketWorkspaceState()
    @Published public private(set) var recentSymbols: [String] = []
    @Published public private(set) var favoriteSymbols: Set<String> = []
    @Published public var searchQuery = ""

    private let financialEngine: FinancialEngine
    private let technicalEngine: TechnicalAnalysisEngine
    private let fundamentalEngine: FundamentalAnalysisEngine
    private let visualizationEngine: VisualizationEngine
    private let advisorEngine: AIAdvisorEngine

    public init(
        financialEngine: FinancialEngine,
        technicalEngine: TechnicalAnalysisEngine,
        fundamentalEngine: FundamentalAnalysisEngine,
        visualizationEngine: VisualizationEngine,
        advisorEngine: AIAdvisorEngine,
        initialLoadingState: MarketWorkspaceLoadingState = .idle
    ) {
        self.financialEngine = financialEngine
        self.technicalEngine = technicalEngine
        self.fundamentalEngine = fundamentalEngine
        self.visualizationEngine = visualizationEngine
        self.advisorEngine = advisorEngine
        loadingState = initialLoadingState
    }

    public func search() async {
        let query = searchQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else {
            loadingState = .empty
            return
        }

        let symbol = query.uppercased()
        if let currentCompany = state.company,
           currentCompany.name.localizedCaseInsensitiveContains(query) {
            await selectSymbol(currentCompany.symbol)
            return
        }
        await selectSymbol(symbol)
    }

    public func selectSymbol(_ symbol: String) async {
        let normalized = symbol.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !normalized.isEmpty else { loadingState = .empty; return }
        loadingState = state.symbol == nil ? .loading : .refreshing

        do {
            try await loadSymbol(normalized)
            if !recentSymbols.contains(normalized) {
                recentSymbols.insert(normalized, at: 0)
                recentSymbols = Array(recentSymbols.prefix(8))
            }
            loadingState = .loaded
            state.lastUpdated = Date()
        } catch let error as MarketWorkspaceError {
            loadingState = error == .notFound ? .empty : .failed(error.description)
        } catch {
            loadingState = .failed("Market data could not be loaded. Please try again. (\(error))")
        }
    }

    public func refresh() async {
        guard let symbol = state.symbol else {
            loadingState = .empty
            return
        }
        await selectSymbol(symbol)
    }

    public func selectRange(_ range: MarketChartRange) async {
        state.selectedRange = range
        guard let symbol = state.symbol else { return }
        do {
            state.history = try await fetchHistory(symbol: symbol, range: range)
            state.priceChart = makePriceChart(history: state.history, symbol: symbol)
        } catch {
            state.history = []
            state.priceChart = nil
        }
    }

    public func toggleFavorite() {
        guard let symbol = state.symbol else { return }
        if favoriteSymbols.contains(symbol) {
            favoriteSymbols.remove(symbol)
        } else {
            favoriteSymbols.insert(symbol)
        }
    }

    public func selectRecent(_ symbol: String) async {
        await selectSymbol(symbol)
    }

    public func refreshNews() async {
        guard let symbol = state.symbol else { return }
        do {
            state.news = try await financialEngine.fetchNews(symbols: [symbol])
        } catch let error as FinancialError where isUnavailable(error) {
            state.news = []
        } catch {
            loadingState = .failed("News could not be loaded. Please try again.")
        }
    }

    public func refreshTechnicalAnalysis() async {
        guard let symbol = state.symbol, !state.history.isEmpty else {
            state.technical = MarketTechnicalState()
            return
        }
        state.technical = await loadTechnical(symbol: symbol, history: state.history)
    }

    public func refreshFundamentalAnalysis() async {
        // FundamentalAnalysisEngine requires statements that current
        // FinancialProvider models do not expose, so no fake report is built.
        _ = fundamentalEngine.config
        state.fundamental = MarketFundamentalState()
    }

    public func refreshAIAnalysis() async {
        state.aiAnalysis = await loadAIAnalysis()
    }

    private func loadSymbol(_ symbol: String) async throws {
        async let quoteResult = fetchQuote(symbol: symbol)
        async let companyResult = fetchCompany(symbol: symbol)
        async let historyResult = fetchHistory(symbol: symbol, range: state.selectedRange)
        async let newsResult = fetchNews(symbol: symbol)
        async let indicesResult = fetchIndices()

        let quote = try await quoteResult
        let company = try await companyResult
        let history = try await historyResult
        let news = try await newsResult
        let indices = try await indicesResult

        state.symbol = symbol
        state.quote = quote
        state.company = company
        state.history = history
        state.priceChart = makePriceChart(history: history, symbol: symbol)
        state.news = news
        state.marketIndices = indices
        state.technical = await loadTechnical(symbol: symbol, history: history)
        state.fundamental = MarketFundamentalState()
        state.aiAnalysis = await loadAIAnalysis()
    }

    private func fetchQuote(symbol: String) async throws -> Quote {
        do { return try await financialEngine.fetchQuote(symbol: symbol) }
        catch let error as FinancialError where isUnavailable(error) { throw MarketWorkspaceError.notFound }
    }

    private func fetchCompany(symbol: String) async throws -> CompanyProfile {
        do { return try await financialEngine.fetchCompanyProfile(symbol: symbol) }
        catch let error as FinancialError where isUnavailable(error) { throw MarketWorkspaceError.notFound }
    }

    private func fetchHistory(symbol: String, range: MarketChartRange) async throws -> [OHLCV] {
        guard let sourceRange = range.sourceRange else { return [] }
        do { return try await financialEngine.fetchOHLCV(symbol: symbol, range: sourceRange) }
        catch let error as FinancialError where isUnavailable(error) { return [] }
    }

    private func fetchNews(symbol: String) async throws -> [NewsArticle] {
        do { return try await financialEngine.fetchNews(symbols: [symbol]) }
        catch let error as FinancialError where isUnavailable(error) { return [] }
    }

    private func fetchIndices() async throws -> [MarketIndex] {
        do { return try await financialEngine.fetchIndices() }
        catch let error as FinancialError where isUnavailable(error) { return [] }
    }

    private func loadTechnical(symbol: String, history: [OHLCV]) async -> MarketTechnicalState {
        guard !history.isEmpty else { return MarketTechnicalState() }
        async let rsi = try? technicalEngine.computeRSI(bars: history, symbol: symbol)
        async let macd = try? technicalEngine.computeMACD(bars: history, symbol: symbol)
        async let ema = try? technicalEngine.computeEMA(bars: history, symbol: symbol)
        async let bands = try? technicalEngine.computeBollingerBands(bars: history, symbol: symbol)
        async let signal = try? technicalEngine.generateSignal(bars: history, symbol: symbol)
        let patterns = technicalEngine.detectPatterns(bars: history)
        return MarketTechnicalState(
            rsi: await rsi,
            macd: await macd,
            movingAverage: await ema,
            bollingerBands: await bands,
            signal: await signal,
            patterns: patterns
        )
    }

    private func makePriceChart(history: [OHLCV], symbol: String) -> ChartData? {
        guard !history.isEmpty else { return nil }
        return visualizationEngine.candlestickChart(history, title: "\(symbol) Price")
    }

    private func loadAIAnalysis() async -> AdvisorResponse? {
        guard let symbol = state.symbol else { return nil }
        let response = await advisorEngine.ask(
            AdvisorRequest(
                question: "Analyze \(symbol) using the available quote, company profile, technical data, and news. Provide a summary, strengths, weaknesses, opportunities, risks, and a suggested action.",
                technicalData: ["signal": state.technical.signal?.strength.rawValue ?? "unavailable"],
                news: state.news
            )
        )
        return response.provider == "none" ? nil : response
    }

    private func isUnavailable(_ error: FinancialError) -> Bool {
        switch error {
        case .providerNotAvailable, .symbolNotFound, .unsupportedCapability: true
        default: false
        }
    }
}

private enum MarketWorkspaceError: Error, CustomStringConvertible, Equatable {
    case notFound

    var description: String {
        switch self {
        case .notFound: "The symbol could not be found."
        }
    }
}
