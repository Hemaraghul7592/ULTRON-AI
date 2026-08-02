import SwiftUI

public struct MarketWorkspaceView: View {
    @StateObject private var viewModel: MarketWorkspaceViewModel

    public init(viewModel: MarketWorkspaceViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    public var body: some View {
        HStack(spacing: 0) {
            MarketSidebar(
                searchQuery: $viewModel.searchQuery,
                favorites: viewModel.favoriteSymbols,
                recentSymbols: viewModel.recentSymbols,
                selectedSymbol: viewModel.state.symbol,
                onSearch: { Task { await viewModel.search() } },
                onSelect: { symbol in Task { await viewModel.selectSymbol(symbol) } }
            )
            Divider()
            mainContent
        }
        .background(Color.black.opacity(0.94))
        .task {
            guard viewModel.loadingState == .idle else { return }
            if !viewModel.searchQuery.isEmpty { await viewModel.search() }
        }
        .toolbar {
            ToolbarItem {
                Button {
                    Task { await viewModel.refresh() }
                } label: {
                    Label("Refresh market", systemImage: "arrow.clockwise")
                }
                .disabled(viewModel.loadingState == .loading || viewModel.loadingState == .refreshing)
                .accessibilityIdentifier("market.toolbar.refresh")
            }
        }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("market.workspace")
    }

    @ViewBuilder
    private var mainContent: some View {
        switch viewModel.loadingState {
        case .idle, .loading:
            MarketLoadingView()
        case .empty:
            EmptySearchView()
        case .failed(let message):
            MarketErrorView(message: message) { Task { await viewModel.refresh() } }
        case .refreshing, .loaded:
            loadedContent
        }
    }

    private var loadedContent: some View {
        VStack(alignment: .leading, spacing: 18) {
            MarketHeader(
                company: viewModel.state.company,
                quote: viewModel.state.quote,
                lastUpdated: viewModel.state.lastUpdated,
                isRefreshing: viewModel.loadingState == .refreshing,
                isFavorite: viewModel.state.symbol.map(viewModel.favoriteSymbols.contains) ?? false,
                onRefresh: { Task { await viewModel.refresh() } },
                onFavorite: viewModel.toggleFavorite
            )

            MarketSearchBar(query: $viewModel.searchQuery) {
                Task { await viewModel.search() }
            }

            ScrollView {
                LazyVGrid(
                    columns: [GridItem(.adaptive(minimum: 320, maximum: 620), spacing: 16)],
                    alignment: .leading,
                    spacing: 16
                ) {
                    QuoteCard(quote: viewModel.state.quote, state: cardState(viewModel.state.quote != nil))
                    MarketWorkspaceOverviewCard(indices: viewModel.state.marketIndices, state: cardState(!viewModel.state.marketIndices.isEmpty))
                    MarketStatusCard(indices: viewModel.state.marketIndices, state: cardState(!viewModel.state.marketIndices.isEmpty))
                    CompanyProfileCard(profile: viewModel.state.company, state: cardState(viewModel.state.company != nil))
                    PriceChartCard(
                        chart: viewModel.state.priceChart,
                        range: viewModel.state.selectedRange,
                        state: cardState(viewModel.state.priceChart != nil),
                        onSelectRange: { range in Task { await viewModel.selectRange(range) } }
                    )
                    TechnicalAnalysisCard(technical: viewModel.state.technical, state: technicalState)
                    FundamentalAnalysisCard(fundamental: viewModel.state.fundamental, state: .empty)
                    NewsFeedCard(news: viewModel.state.news, state: cardState(!viewModel.state.news.isEmpty), onRefresh: { Task { await viewModel.refreshNews() } })
                    AIAnalysisCard(analysis: viewModel.state.aiAnalysis, state: cardState(viewModel.state.aiAnalysis != nil), onRefresh: { Task { await viewModel.refreshAIAnalysis() } })
                    RelatedCompaniesCard(state: .empty)
                }
                .padding(.bottom, 18)
            }
            .scrollIndicators(.hidden)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private var technicalState: DashboardCardState {
        let technical = viewModel.state.technical
        let hasData = technical.rsi != nil || technical.macd != nil || technical.movingAverage != nil || technical.bollingerBands != nil || technical.signal != nil
        return cardState(hasData)
    }

    private func cardState(_ hasContent: Bool) -> DashboardCardState {
        switch viewModel.loadingState {
        case .idle, .loading: .loading
        case .refreshing: hasContent ? .loaded : .loading
        case .loaded: hasContent ? .loaded : .empty
        case .empty: .empty
        case .failed(let message): .failed(message)
        }
    }
}

private struct MarketLoadingView: View {
    var body: some View {
        VStack(spacing: 14) {
            ProgressView()
            Text("Loading market workspace...").foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityLabel("Loading market workspace")
    }
}

private struct MarketErrorView: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("Market unavailable", systemImage: "exclamationmark.triangle")
        } description: {
            Text(message)
        } actions: {
            Button("Retry", action: retry)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#if DEBUG
#Preview("Market Empty") {
    MarketWorkspaceView(viewModel: MarketWorkspacePreviewFactory.make(state: .empty))
        .frame(width: 1280, height: 800)
}

#Preview("Market Loading") {
    MarketWorkspaceView(viewModel: MarketWorkspacePreviewFactory.make(state: .loading))
        .frame(width: 900, height: 650)
}

#Preview("Market Error") {
    MarketWorkspaceView(viewModel: MarketWorkspacePreviewFactory.make(state: .failed("Preview error")))
        .frame(width: 1440, height: 900)
}
#endif
