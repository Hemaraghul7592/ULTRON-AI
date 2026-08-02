import SwiftUI

public struct EmptySearchView: View {
    public init() {}

    public var body: some View {
        ContentUnavailableView {
            Label("Search the market", systemImage: "magnifyingglass")
        } description: {
            Text("Enter a company symbol or name to load quotes, charts, analysis, and news.")
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityIdentifier("market.empty-search")
    }
}

#if DEBUG
enum MarketWorkspacePreviewFactory {
    enum PreviewState { case loading, empty, failed(String) }

    @MainActor
    static func make(state: PreviewState) -> MarketWorkspaceViewModel {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let loadingState: MarketWorkspaceLoadingState
        switch state {
        case .loading: loadingState = .loading
        case .empty: loadingState = .empty
        case .failed(let message): loadingState = .failed(message)
        }
        return MarketWorkspaceViewModel(
            financialEngine: FinancialEngine(logger: logger),
            technicalEngine: TechnicalAnalysisEngine(),
            fundamentalEngine: FundamentalAnalysisEngine(),
            visualizationEngine: VisualizationEngine(logger: logger),
            advisorEngine: AIAdvisorEngine(primary: MockLLMProvider(), fallback: MockLLMProvider(), logger: logger),
            initialLoadingState: loadingState
        )
    }
}
#endif
