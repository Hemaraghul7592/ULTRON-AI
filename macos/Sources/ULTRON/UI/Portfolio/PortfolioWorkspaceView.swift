import SwiftUI

public struct PortfolioWorkspaceView: View {
    @StateObject private var viewModel: PortfolioWorkspaceViewModel

    public init(viewModel: PortfolioWorkspaceViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    public var body: some View {
        HStack(spacing: 0) {
            PortfolioSidebar(
                portfolios: viewModel.portfolios,
                watchlists: viewModel.watchlists,
                selectedPortfolioID: viewModel.selectedPortfolioID,
                onSelectPortfolio: { id in
                    Task { await viewModel.selectPortfolio(id: id) }
                }
            )
            Divider()
            workspaceContent
        }
        .background(Color.black.opacity(0.94))
        .task {
            guard viewModel.loadingState == .idle else { return }
            await viewModel.loadWorkspace()
        }
        .toolbar {
            ToolbarItem {
                Button {
                    Task { await viewModel.refresh() }
                } label: {
                    Label("Refresh portfolio", systemImage: "arrow.clockwise")
                }
                .disabled(viewModel.loadingState == .loading || viewModel.loadingState == .refreshing)
                .accessibilityIdentifier("portfolio.toolbar.refresh")
            }
        }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("portfolio.workspace")
    }

    @ViewBuilder
    private var workspaceContent: some View {
        switch viewModel.loadingState {
        case .idle, .loading:
            PortfolioWorkspaceLoadingView()
        case .empty:
            EmptyPortfolioView()
        case .failed(let message):
            PortfolioWorkspaceErrorView(message: message) {
                Task { await viewModel.refresh() }
            }
        case .refreshing, .loaded:
            loadedWorkspace
        }
    }

    private var loadedWorkspace: some View {
        VStack(alignment: .leading, spacing: 18) {
            PortfolioHeader(
                portfolio: viewModel.selectedPortfolio,
                summary: viewModel.summary,
                lastUpdated: viewModel.lastUpdated,
                isRefreshing: viewModel.loadingState == .refreshing,
                searchText: $viewModel.searchText,
                sort: $viewModel.sort,
                filter: $viewModel.filter,
                onRefresh: { Task { await viewModel.refresh() } }
            )

            ScrollView {
                LazyVGrid(
                    columns: [GridItem(.adaptive(minimum: 320, maximum: 620), spacing: 16)],
                    alignment: .leading,
                    spacing: 16
                ) {
                    PortfolioWorkspaceSummaryCard(summary: viewModel.summary, state: cardState(viewModel.summary != nil))
                    PortfolioPerformanceCard(chart: viewModel.performanceChart, state: cardState(viewModel.performanceChart != nil))
                    PortfolioWorkspaceAllocationCard(chart: viewModel.allocationChart, state: cardState(viewModel.allocationChart != nil))
                    PortfolioAnalyticsCard(analytics: viewModel.analytics, state: cardState(viewModel.summary != nil))
                    TransactionHistoryCard(transactions: viewModel.transactions, state: cardState(!viewModel.transactions.isEmpty))
                    PortfolioWorkspaceWatchlistCard(watchlists: viewModel.watchlists, state: cardState(!viewModel.watchlists.isEmpty))
                    PortfolioAIReviewCard(review: viewModel.aiReview, state: cardState(viewModel.aiReview != nil))
                }
                .padding(.bottom, 18)

                HoldingsTable(
                    rows: viewModel.displayedHoldings,
                    state: cardState(!viewModel.holdings.isEmpty),
                    selectedHoldingID: viewModel.selectedHoldingID,
                    onSelect: viewModel.selectHolding(id:)
                )
            }
            .scrollIndicators(.hidden)
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private func cardState(_ hasContent: Bool) -> DashboardCardState {
        switch viewModel.loadingState {
        case .idle, .loading:
            .loading
        case .refreshing:
            hasContent ? .loaded : .loading
        case .loaded:
            hasContent ? .loaded : .empty
        case .empty:
            .empty
        case .failed(let message):
            .failed(message)
        }
    }
}

private struct PortfolioWorkspaceLoadingView: View {
    var body: some View {
        VStack(spacing: 14) {
            ProgressView()
            Text("Loading portfolio workspace...")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Loading portfolio workspace")
    }
}

private struct PortfolioWorkspaceErrorView: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        ContentUnavailableView {
            Label("Portfolio unavailable", systemImage: "exclamationmark.triangle")
        } description: {
            Text(message)
        } actions: {
            Button("Retry", action: retry)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#if DEBUG
#Preview("Portfolio Empty") {
    PortfolioWorkspaceView(viewModel: PortfolioWorkspacePreviewFactory.make(state: .empty))
        .frame(width: 1280, height: 800)
}

#Preview("Portfolio Loading") {
    PortfolioWorkspaceView(viewModel: PortfolioWorkspacePreviewFactory.make(state: .loading))
        .frame(width: 900, height: 650)
}

#Preview("Portfolio Error") {
    PortfolioWorkspaceView(viewModel: PortfolioWorkspacePreviewFactory.make(state: .failed("Preview error")))
        .frame(width: 1440, height: 900)
}
#endif
