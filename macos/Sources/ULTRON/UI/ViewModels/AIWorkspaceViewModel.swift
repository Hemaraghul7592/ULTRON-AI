import Foundation
import SwiftUI

public enum AIWorkspaceState: Equatable, Sendable {
    case idle, loading, thinking, streamingReady, completed, cancelled, failed(String)
}

public enum AIAction: String, CaseIterable, Sendable {
    case researchCompany = "Research Company"
    case openPortfolio = "Open Portfolio"
    case showTechnicals = "Show Technicals"
    case openFundamentals = "Open Fundamentals"
    case createAlert = "Create Alert"
    case addWatchlist = "Add Watchlist"
    case copySummary = "Copy Summary"
}

public struct AIWorkspaceContext: Sendable {
    public let portfolio: PortfolioSummary?
    public let watchlists: [Watchlist]
    public let marketIndices: [MarketIndex]
    public let news: [NewsArticle]
    public let technicalSummary: String?
    public let fundamentalSummary: String?
    public let alerts: [Alert]
    public init(portfolio: PortfolioSummary? = nil, watchlists: [Watchlist] = [], marketIndices: [MarketIndex] = [], news: [NewsArticle] = [], technicalSummary: String? = nil, fundamentalSummary: String? = nil, alerts: [Alert] = []) {
        self.portfolio = portfolio; self.watchlists = watchlists; self.marketIndices = marketIndices; self.news = news; self.technicalSummary = technicalSummary; self.fundamentalSummary = fundamentalSummary; self.alerts = alerts
    }
}

@MainActor
public final class AIWorkspaceViewModel: ObservableObject {
    @Published public private(set) var state: AIWorkspaceState = .idle
    @Published public private(set) var context = AIWorkspaceContext()
    @Published public private(set) var messages: [ConversationEntry] = []
    @Published public private(set) var latestResponse: AdvisorResponse?
    @Published public private(set) var suggestions: [String] = []
    @Published public private(set) var actions = AIAction.allCases
    @Published public private(set) var recommendations: [Recommendation] = []
    @Published public var input = ""
    @Published public private(set) var pendingQuestion: String?

    private let advisorEngine: AIAdvisorEngine
    private let financialEngine: FinancialEngine
    private let portfolioEngine: PortfolioEngine
    private let technicalEngine: TechnicalAnalysisEngine
    private let fundamentalEngine: FundamentalAnalysisEngine
    private let visualizationEngine: VisualizationEngine
    private let alertEngine: AlertEngine
    private let conversationMemory: ConversationMemory
    private var requestTask: Task<Void, Never>?
    private var lastRequest: AdvisorRequest?

    public init(advisorEngine: AIAdvisorEngine, financialEngine: FinancialEngine, portfolioEngine: PortfolioEngine, technicalEngine: TechnicalAnalysisEngine, fundamentalEngine: FundamentalAnalysisEngine, visualizationEngine: VisualizationEngine, alertEngine: AlertEngine, conversationMemory: ConversationMemory, initialState: AIWorkspaceState = .idle) {
        self.advisorEngine = advisorEngine; self.financialEngine = financialEngine; self.portfolioEngine = portfolioEngine; self.technicalEngine = technicalEngine; self.fundamentalEngine = fundamentalEngine; self.visualizationEngine = visualizationEngine; self.alertEngine = alertEngine; self.conversationMemory = conversationMemory
        state = initialState
    }

    public func loadWorkspace() async {
        guard state == .idle else { return }
        state = .loading
        await refreshContext()
        messages = await advisorEngine.getHistory()
        suggestions = makeSuggestions()
        state = .completed
    }

    public func refreshContext() async {
        async let portfolio = loadPortfolio()
        async let watchlists = loadWatchlists()
        async let indices = loadIndices()
        async let news = loadNews()
        async let alerts = alertEngine.getActive()
        let loadedPortfolio = await portfolio
        let loadedWatchlists = await watchlists
        let loadedIndices = await indices
        let loadedNews = await news
        let loadedAlerts = await alerts
        let symbol = loadedWatchlists.flatMap { $0.symbols.map(\.symbol) }.first
        let technical = await loadTechnical(symbol: symbol)
        context = AIWorkspaceContext(portfolio: loadedPortfolio, watchlists: loadedWatchlists, marketIndices: loadedIndices, news: loadedNews, technicalSummary: technical, fundamentalSummary: nil, alerts: loadedAlerts)
        recommendations = loadedPortfolio.map { advisorEngine.recommend(portfolio: $0) } ?? []
        suggestions = makeSuggestions()
    }

    public func send() async {
        let question = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !question.isEmpty else { return }
        input = ""
        await send(question: question)
    }

    public func send(question: String) async {
        guard requestTask == nil else { return }
        pendingQuestion = question
        state = .thinking
        requestTask = Task { @MainActor [weak self] in
            guard let self else { return }
            await self.refreshContext()
            guard !Task.isCancelled else { return }
            let watchlistContext = context.watchlists.map { "\($0.name): \($0.symbols.map(\.symbol).joined(separator: ", "))" }.joined(separator: " | ")
            let alertContext = context.alerts.map(\.title).joined(separator: " | ")
            let marketContext = context.marketIndices.map { "\($0.name): \($0.changePercent.formatted(.percent))" }.joined(separator: ", ")
            let economicContext = "Market: \(marketContext.isEmpty ? "unavailable" : marketContext)\nWatchlists: \(watchlistContext.isEmpty ? "unavailable" : watchlistContext)\nAlerts: \(alertContext.isEmpty ? "none" : alertContext)"
            let request = AdvisorRequest(question: question, portfolioSnapshot: context.portfolio, technicalData: ["summary": context.technicalSummary ?? "unavailable"], fundamentalData: ["summary": context.fundamentalSummary ?? "unavailable"], news: context.news, economicContext: economicContext)
            lastRequest = request
            await submit(request: request, retrying: false)
        }
        let task = requestTask
        await task?.value
        if requestTask != nil { requestTask = nil }
    }

    public func retry() async {
        guard requestTask == nil, let request = lastRequest else { return }
        await submit(request: request, retrying: true)
    }
    public func cancel() { requestTask?.cancel(); requestTask = nil; pendingQuestion = nil; state = .cancelled }
    public func clearConversation() async { requestTask?.cancel(); requestTask = nil; await advisorEngine.clearHistory(); messages = []; latestResponse = nil; pendingQuestion = nil; lastRequest = nil; state = .idle; suggestions = makeSuggestions() }
    public func refreshAI() async { await send(question: "Refresh my investment insight using the latest available context.") }

    private func submit(request: AdvisorRequest, retrying: Bool) async {
        state = .streamingReady
        do {
            let response = try await (retrying ? advisorEngine.retryCancellable(request) : advisorEngine.askCancellable(request))
            guard !Task.isCancelled else { return }
            latestResponse = response.provider == "none" ? nil : response
            messages = await advisorEngine.getHistory()
            pendingQuestion = nil
            state = response.provider == "none" ? .failed("AI providers are currently unavailable.") : .completed
        } catch is CancellationError {
            messages = await advisorEngine.getHistory()
            pendingQuestion = nil
            state = .cancelled
        } catch {
            messages = await advisorEngine.getHistory()
            pendingQuestion = nil
            state = .failed("AI request failed.")
        }
    }

    public func action(_ action: AIAction) -> String {
        switch action {
        case .copySummary: return latestResponse?.summary ?? "No AI summary available."
        case .researchCompany: return "Research is available from the Research workspace."
        case .openPortfolio: return "Portfolio is available from the Portfolio workspace."
        case .showTechnicals: return context.technicalSummary ?? "Technical data is unavailable."
        case .openFundamentals: return context.fundamentalSummary ?? "Fundamental data is unavailable."
        case .createAlert: return "Alert creation is not connected to the current AI workspace."
        case .addWatchlist: return "Watchlist actions are not connected to the current AI workspace."
        }
    }

    public func exportMarkdown() -> String { messages.map { "\($0.role == .user ? "**You**" : "**ULTRON**"): \($0.content)" }.joined(separator: "\n\n") }
    public func exportJSON() -> Data? { try? JSONEncoder().encode(messages) }

    private func loadPortfolio() -> PortfolioSummary? { portfolioEngine.getAllPortfolios().compactMap { portfolioEngine.summary(for: $0.id) }.first }
    private func loadWatchlists() -> [Watchlist] { portfolioEngine.getAllWatchlists() }
    private func loadIndices() async -> [MarketIndex] { (try? await financialEngine.fetchIndices()) ?? [] }
    private func loadNews() async -> [NewsArticle] { (try? await financialEngine.fetchNews()) ?? [] }
    private func loadTechnical(symbol: String?) async -> String? {
        guard let symbol else { return nil }
        guard let bars = try? await financialEngine.fetchOHLCV(symbol: symbol, range: .oneMonth), !bars.isEmpty else { return nil }
        let signal = try? await technicalEngine.generateSignal(bars: bars, symbol: symbol)
        return signal.map { "\(symbol): \($0.strength.rawValue), confidence \($0.confidence.formatted(.percent))" }
    }
private func makeSuggestions() -> [String] {
        var result = ["Analyze my portfolio", "Risk analysis", "Generate investment thesis"]
        if !context.news.isEmpty { result.insert("Review today's market", at: 1) }
        if !context.watchlists.isEmpty { result.append("Summarize watchlist") }
        if context.portfolio != nil { result.append("What should I rebalance?") }
        return result
    }
}

#if DEBUG
enum AIPreviewFactory {
    enum PreviewState { case idle, thinking }
    @MainActor static func make(state: PreviewState) -> AIWorkspaceViewModel {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let memory = ConversationMemory()
        let ai = MockLLMProvider(response: "Preview response")
        let initialState: AIWorkspaceState
        switch state {
        case .idle: initialState = .idle
        case .thinking: initialState = .thinking
        }
        return AIWorkspaceViewModel(advisorEngine: AIAdvisorEngine(primary: ai, fallback: ai, memory: memory, logger: logger), financialEngine: FinancialEngine(logger: logger), portfolioEngine: PortfolioEngine(storage: InMemoryStorage(), logger: logger), technicalEngine: TechnicalAnalysisEngine(), fundamentalEngine: FundamentalAnalysisEngine(), visualizationEngine: VisualizationEngine(logger: logger), alertEngine: AlertEngine(logger: logger), conversationMemory: memory, initialState: initialState)
    }
}
#endif
