import SwiftUI

public struct EmptyPortfolioView: View {
    public init() {}

    public var body: some View {
        ContentUnavailableView {
            Label("No portfolios yet", systemImage: "briefcase")
        } description: {
            Text("Create a portfolio in PortfolioEngine to start tracking holdings and performance.")
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityIdentifier("portfolio.empty")
    }
}

#if DEBUG
enum PortfolioWorkspacePreviewFactory {
    enum PreviewState {
        case loading
        case empty
        case failed(String)
    }

    @MainActor
    static func make(state: PreviewState) -> PortfolioWorkspaceViewModel {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let portfolioEngine = PortfolioEngine(storage: InMemoryStorage(), logger: logger)
        let ai = MockLLMProvider()
        let loadingState: PortfolioWorkspaceLoadingState
        switch state {
        case .loading: loadingState = .loading
        case .empty: loadingState = .empty
        case .failed(let message): loadingState = .failed(message)
        }
        return PortfolioWorkspaceViewModel(
            portfolioEngine: portfolioEngine,
            financialEngine: FinancialEngine(logger: logger),
            visualizationEngine: VisualizationEngine(logger: logger),
            advisorEngine: AIAdvisorEngine(primary: ai, fallback: ai, logger: logger),
            initialLoadingState: loadingState
        )
    }
}
#endif
