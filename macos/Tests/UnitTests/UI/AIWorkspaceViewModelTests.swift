import Foundation
import Testing

@testable import ULTRON

@MainActor
@Suite struct AIWorkspaceViewModelTests {
    @Test("Workspace loads context and conversation memory")
    func contextAndMemory() async {
        let setup = makeViewModel()
        let portfolio = setup.portfolioEngine.createPortfolio(name: "Primary", cash: 1_000)
        let watchlist = setup.portfolioEngine.createWatchlist(name: "Core")
        try? setup.portfolioEngine.addToWatchlist(watchlistID: watchlist.id, symbol: "TEST")

        await setup.viewModel.loadWorkspace()
        await setup.viewModel.send(question: "Analyze my portfolio")

        #expect(setup.viewModel.context.portfolio != nil)
        #expect(setup.viewModel.context.watchlists.count == 1)
        #expect(setup.viewModel.messages.count == 2)
        #expect(setup.viewModel.latestResponse?.summary == "Injected response")
        #expect(portfolio.name == "Primary")
    }

    @Test("Empty workspace exposes suggestions")
    func emptyState() async {
        let viewModel = makeViewModel().viewModel
        await viewModel.loadWorkspace()

        #expect(viewModel.state == .completed)
        #expect(!viewModel.suggestions.isEmpty)
        #expect(viewModel.context.portfolio == nil)
    }

    @Test("Failed AI provider produces failed state")
    func failure() async {
        let provider = MockLLMProvider(response: "Unavailable")
        await provider.setAvailable(false)
        let viewModel = makeViewModel(primary: provider, fallback: provider).viewModel

        await viewModel.send(question: "What happened today?")

        if case .failed = viewModel.state {
            #expect(viewModel.state != .completed)
        } else {
            Issue.record("Expected failed AI state")
        }
    }

    @Test("Retry reuses the previous user question")
    func retry() async {
        let viewModel = makeViewModel().viewModel
        await viewModel.send(question: "Explain today's losses")
        await viewModel.retry()

        #expect(viewModel.state == .completed)
        #expect(viewModel.messages.count == 4)
    }

    @Test("Cancellation publishes cancelled state")
    func cancellation() {
        let viewModel = makeViewModel().viewModel
        viewModel.cancel()
        #expect(viewModel.state == .cancelled)
    }

    @Test("Action cards expose existing context and export data")
    func actionsAndExport() async {
        let viewModel = makeViewModel().viewModel
        await viewModel.send(question: "Analyze AAPL")

        #expect(viewModel.action(.copySummary) == "Injected response")
        #expect(!viewModel.exportMarkdown().isEmpty)
        #expect(viewModel.exportJSON() != nil)
    }

    private func makeViewModel(primary: MockLLMProvider? = nil, fallback: MockLLMProvider? = nil) -> (viewModel: AIWorkspaceViewModel, portfolioEngine: PortfolioEngine) {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let memory = ConversationMemory()
        let primaryProvider = primary ?? MockLLMProvider(response: "Injected response")
        let fallbackProvider = fallback ?? primaryProvider
        let advisor = AIAdvisorEngine(primary: primaryProvider, fallback: fallbackProvider, memory: memory, logger: logger)
        let portfolioEngine = PortfolioEngine(storage: InMemoryStorage(), logger: logger)
        return (
            AIWorkspaceViewModel(
                advisorEngine: advisor,
                financialEngine: FinancialEngine(logger: logger),
                portfolioEngine: portfolioEngine,
                technicalEngine: TechnicalAnalysisEngine(),
                fundamentalEngine: FundamentalAnalysisEngine(),
                visualizationEngine: VisualizationEngine(logger: logger),
                alertEngine: AlertEngine(logger: logger),
                conversationMemory: memory
            ),
            portfolioEngine
        )
    }
}
