import SwiftUI

public struct EmptyResearchView: View {
    public init() {}
    public var body: some View { ContentUnavailableView { Label("Start company research", systemImage: "doc.text.magnifyingglass") } description: { Text("Search for a company symbol to build an evidence-based research report.") }.frame(maxWidth: .infinity, maxHeight: .infinity).accessibilityIdentifier("research.empty") }
}

#if DEBUG
enum ResearchPreviewFactory {
    enum PreviewState { case loading, empty, failed(String) }
    @MainActor static func make(state: PreviewState) -> ResearchWorkspaceViewModel {
        let logger = Logger(configuration: .init(minimumLevel: .error))
        let loading: ResearchWorkspaceLoadingState = switch state { case .loading: .loading; case .empty: .empty; case .failed(let message): .failed(message) }
        let ai = MockLLMProvider()
        return ResearchWorkspaceViewModel(financialEngine: FinancialEngine(logger: logger), fundamentalEngine: FundamentalAnalysisEngine(), technicalEngine: TechnicalAnalysisEngine(), visualizationEngine: VisualizationEngine(logger: logger), advisorEngine: AIAdvisorEngine(primary: ai, fallback: ai, logger: logger), portfolioEngine: PortfolioEngine(storage: InMemoryStorage(), logger: logger), initialLoadingState: loading)
    }
}
#endif
