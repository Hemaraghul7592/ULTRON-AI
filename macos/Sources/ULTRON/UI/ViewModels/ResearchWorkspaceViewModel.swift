import Foundation
import SwiftUI

public enum ResearchWorkspaceLoadingState: Equatable, Sendable {
    case idle, loading, loaded, refreshing, empty, failed(String)
}

public enum ResearchChecklistStatus: String, Sendable {
    case pass = "Pass"
    case warning = "Warning"
    case unavailable = "Unavailable"
}

public struct ResearchChecklistItem: Identifiable, Sendable {
    public let id: String
    public let title: String
    public let status: ResearchChecklistStatus
    public init(id: String = UUID().uuidString, title: String, status: ResearchChecklistStatus) {
        self.id = id; self.title = title; self.status = status
    }
}

public struct ResearchTimelineEvent: Identifiable, Sendable {
    public let id: String
    public let title: String
    public let detail: String
    public let date: Date
    public init(id: String = UUID().uuidString, title: String, detail: String, date: Date) {
        self.id = id; self.title = title; self.detail = detail; self.date = date
    }
}

public struct ResearchFundamentalState: Sendable {
    public let valuation: RatioReport?
    public let intrinsicValue: ValuationResult?
    public let score: FundamentalScore?
    public let profitability: ProfitabilityReport?
    public let growth: GrowthReport?
    public init(valuation: RatioReport? = nil, intrinsicValue: ValuationResult? = nil, score: FundamentalScore? = nil, profitability: ProfitabilityReport? = nil, growth: GrowthReport? = nil) {
        self.valuation = valuation; self.intrinsicValue = intrinsicValue; self.score = score; self.profitability = profitability; self.growth = growth
    }
}

@MainActor
public final class ResearchWorkspaceViewModel: ObservableObject {
    @Published public private(set) var loadingState: ResearchWorkspaceLoadingState = .idle
    @Published public private(set) var symbol: String?
    @Published public private(set) var quote: Quote?
    @Published public private(set) var company: CompanyProfile?
    @Published public private(set) var history: [OHLCV] = []
    @Published public private(set) var chart: ChartData?
    @Published public private(set) var technical = MarketTechnicalState()
    @Published public private(set) var fundamental = ResearchFundamentalState()
    @Published public private(set) var news: [NewsArticle] = []
    @Published public private(set) var aiResearch: AdvisorResponse?
    @Published public private(set) var portfolioExposure: PortfolioSummary?
    @Published public private(set) var checklist: [ResearchChecklistItem] = []
    @Published public private(set) var timeline: [ResearchTimelineEvent] = []
    @Published public private(set) var lastUpdated: Date?
    @Published public private(set) var recentSymbols: [String] = []
    @Published public private(set) var favoriteSymbols: Set<String> = []
    @Published public var searchQuery = ""
    @Published public var notes = ""

    private let financialEngine: FinancialEngine
    private let fundamentalEngine: FundamentalAnalysisEngine
    private let technicalEngine: TechnicalAnalysisEngine
    private let visualizationEngine: VisualizationEngine
    private let advisorEngine: AIAdvisorEngine
    private let portfolioEngine: PortfolioEngine
    private var notesBySymbol: [String: String] = [:]

    public init(financialEngine: FinancialEngine, fundamentalEngine: FundamentalAnalysisEngine, technicalEngine: TechnicalAnalysisEngine, visualizationEngine: VisualizationEngine, advisorEngine: AIAdvisorEngine, portfolioEngine: PortfolioEngine, initialLoadingState: ResearchWorkspaceLoadingState = .idle) {
        self.financialEngine = financialEngine; self.fundamentalEngine = fundamentalEngine; self.technicalEngine = technicalEngine; self.visualizationEngine = visualizationEngine; self.advisorEngine = advisorEngine; self.portfolioEngine = portfolioEngine
        loadingState = initialLoadingState
    }

    public func search() async {
        let query = searchQuery.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { loadingState = .empty; return }
        await selectSymbol(query.uppercased())
    }

    public func selectSymbol(_ value: String) async {
        let normalized = value.trimmingCharacters(in: .whitespacesAndNewlines).uppercased()
        guard !normalized.isEmpty else { loadingState = .empty; return }
        loadingState = symbol == nil ? .loading : .refreshing
        do {
            async let quoteResult = fetchQuote(normalized)
            async let companyResult = fetchCompany(normalized)
            async let historyResult = fetchHistory(normalized)
            async let newsResult = fetchNews(normalized)
            let loadedQuote = try await quoteResult
            let loadedCompany = try await companyResult
            let loadedHistory = try await historyResult
            let loadedNews = try await newsResult
            symbol = normalized; quote = loadedQuote; company = loadedCompany; history = loadedHistory; news = loadedNews
            chart = loadedHistory.isEmpty ? nil : visualizationEngine.candlestickChart(loadedHistory, title: "\(normalized) Research")
            technical = await loadTechnical(normalized, bars: loadedHistory)
            fundamental = ResearchFundamentalState()
            portfolioExposure = portfolioEngine.getAllPortfolios().compactMap { portfolioEngine.summary(for: $0.id) }.first { $0.topHolding == normalized }
            aiResearch = await loadAIResearch()
            checklist = makeChecklist()
            timeline = loadedNews.map { ResearchTimelineEvent(title: $0.title, detail: $0.source, date: $0.publishedAt) }.sorted { $0.date > $1.date }
            notes = notesBySymbol[normalized] ?? ""
            if !recentSymbols.contains(normalized) { recentSymbols.insert(normalized, at: 0); recentSymbols = Array(recentSymbols.prefix(8)) }
            loadingState = .loaded; lastUpdated = Date()
        } catch let error as ResearchError where error == .notFound {
            loadingState = .empty
        } catch {
            loadingState = .failed("Research could not be loaded. Please try again. (\(error))")
        }
    }

    public func refresh() async { guard let symbol else { loadingState = .empty; return }; await selectSymbol(symbol) }
    public func refreshAIAnalysis() async { aiResearch = await loadAIResearch() }
    public func refreshTechnicalAnalysis() async { technical = await loadTechnical(symbol ?? "", bars: history) }
    public func refreshFundamentalAnalysis() async { fundamental = ResearchFundamentalState(); _ = fundamentalEngine.config }
    public func refreshNews() async { guard let symbol else { return }; news = (try? await fetchNews(symbol)) ?? []; timeline = news.map { ResearchTimelineEvent(title: $0.title, detail: $0.source, date: $0.publishedAt) }.sorted { $0.date > $1.date } }
    public func toggleFavorite() { guard let symbol else { return }; if favoriteSymbols.contains(symbol) { favoriteSymbols.remove(symbol) } else { favoriteSymbols.insert(symbol) } }
    public func selectRecent(_ symbol: String) async { await selectSymbol(symbol) }
    public func saveNotes() { guard let symbol else { return }; notesBySymbol[symbol] = notes }

    public func copySummary() -> String { summaryText }
    public func exportMarkdown() -> String { "# \(company?.name ?? symbol ?? "Research")\n\n\(summaryText)\n\n## Notes\n\(notes)" }
    public func exportJSON() -> Data? { try? JSONEncoder().encode(ResearchExport(symbol: symbol, quote: quote, company: company, news: news, notes: notes)) }

    private var summaryText: String { "\(company?.name ?? symbol ?? "Company") (\(symbol ?? ""))\nPrice: \(quote?.price.formatted() ?? "Unavailable")\nSector: \(company?.sector.isEmpty == false ? company?.sector ?? "" : "Unavailable")\nIndustry: \(company?.industry.isEmpty == false ? company?.industry ?? "" : "Unavailable")" }
    private func fetchQuote(_ symbol: String) async throws -> Quote {
        do { return try await financialEngine.fetchQuote(symbol: symbol) }
        catch let error as FinancialError where isUnavailable(error) { throw ResearchError.notFound }
    }
    private func fetchCompany(_ symbol: String) async throws -> CompanyProfile {
        do { return try await financialEngine.fetchCompanyProfile(symbol: symbol) }
        catch let error as FinancialError where isUnavailable(error) { throw ResearchError.notFound }
    }
    private func fetchHistory(_ symbol: String) async throws -> [OHLCV] { (try? await financialEngine.fetchOHLCV(symbol: symbol, range: .oneMonth)) ?? [] }
    private func fetchNews(_ symbol: String) async throws -> [NewsArticle] { (try? await financialEngine.fetchNews(symbols: [symbol])) ?? [] }

    private func loadTechnical(_ symbol: String, bars: [OHLCV]) async -> MarketTechnicalState {
        guard !bars.isEmpty else { return MarketTechnicalState() }
        async let rsi = try? technicalEngine.computeRSI(bars: bars, symbol: symbol)
        async let macd = try? technicalEngine.computeMACD(bars: bars, symbol: symbol)
        async let ema = try? technicalEngine.computeEMA(bars: bars, symbol: symbol)
        async let bands = try? technicalEngine.computeBollingerBands(bars: bars, symbol: symbol)
        async let signal = try? technicalEngine.generateSignal(bars: bars, symbol: symbol)
        return MarketTechnicalState(rsi: await rsi, macd: await macd, movingAverage: await ema, bollingerBands: await bands, signal: await signal, patterns: technicalEngine.detectPatterns(bars: bars))
    }

    private func loadAIResearch() async -> AdvisorResponse? {
        guard let symbol else { return nil }
        let response = await advisorEngine.ask(AdvisorRequest(question: "Prepare an investment research report for \(symbol), including executive summary, bull case, bear case, key risks, investment thesis, and suggested strategy.", technicalData: ["signal": technical.signal?.strength.rawValue ?? "unavailable"], news: news))
        return response.provider == "none" ? nil : response
    }

    private func isUnavailable(_ error: FinancialError) -> Bool {
        switch error {
        case .providerNotAvailable, .symbolNotFound, .unsupportedCapability: true
        default: false
        }
    }

    private func makeChecklist() -> [ResearchChecklistItem] {
        [
            ResearchChecklistItem(title: "Revenue growing", status: .unavailable),
            ResearchChecklistItem(title: "Profitable", status: .unavailable),
            ResearchChecklistItem(title: "Healthy balance sheet", status: .unavailable),
            ResearchChecklistItem(title: "Reasonable valuation", status: fundamental.valuation == nil ? .unavailable : .pass),
            ResearchChecklistItem(title: "Strong momentum", status: technical.signal == nil ? .unavailable : .pass),
            ResearchChecklistItem(title: "Positive news", status: news.isEmpty ? .unavailable : .pass),
            ResearchChecklistItem(title: "AI confidence", status: aiResearch?.confidence == nil || aiResearch?.confidence == 0 ? .unavailable : .pass)
        ]
    }
}

private enum ResearchError: Error, Equatable { case notFound }
private struct ResearchExport: Codable { let symbol: String?; let quote: Quote?; let company: CompanyProfile?; let news: [NewsArticle]; let notes: String }
