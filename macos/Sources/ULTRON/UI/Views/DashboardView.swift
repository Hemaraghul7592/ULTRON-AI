import SwiftUI

/// Premium dashboard surface. All data is supplied by `DashboardViewModel`.
public struct DashboardView: View {
    @StateObject private var viewModel: DashboardViewModel

    public init(viewModel: DashboardViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            DashboardHeader(
                marketStatus: viewModel.state.marketStatus,
                lastUpdated: viewModel.state.lastUpdated,
                isRefreshing: viewModel.loadingState == .loading,
                onRefresh: refresh
            )

            Group {
                switch viewModel.loadingState {
                case .idle, .loading:
                    dashboardGrid
                case .loaded:
                    dashboardGrid
                case .failed:
                    dashboardGrid
                }
            }
        }
        .padding(.horizontal, 28)
        .padding(.vertical, 24)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .background(Color.black.opacity(0.94))
        .task {
            guard viewModel.loadingState == .idle else { return }
            await viewModel.loadDashboard()
        }
        .toolbar {
            ToolbarItem {
                Button(action: refresh) {
                    Label("Refresh dashboard", systemImage: "arrow.clockwise")
                }
                .disabled(viewModel.loadingState == .loading)
                .accessibilityIdentifier("dashboard.toolbar.refresh")
            }
        }
        .preferredColorScheme(.dark)
        .accessibilityIdentifier("dashboard.view")
    }

    private var dashboardGrid: some View {
        ScrollView {
            LazyVGrid(
                columns: [GridItem(.adaptive(minimum: 310, maximum: 560), spacing: 16)],
                alignment: .leading,
                spacing: 16
            ) {
                PortfolioSummaryCard(
                    summary: viewModel.state.selectedPortfolioSummary,
                    state: cardState(hasContent: viewModel.state.selectedPortfolioSummary != nil)
                )

                MarketOverviewCard(
                    status: viewModel.state.marketStatus,
                    state: cardState(hasContent: viewModel.state.marketStatus == .available)
                )

                PortfolioAllocationCard(
                    chart: viewModel.state.portfolioAllocation,
                    state: cardState(hasContent: viewModel.state.portfolioAllocation != nil)
                )

                AlertCard(
                    alerts: viewModel.state.activeAlerts,
                    state: cardState(hasContent: !viewModel.state.activeAlerts.isEmpty)
                )

                NewsCard(
                    articles: viewModel.state.latestFinancialNews,
                    state: cardState(hasContent: !viewModel.state.latestFinancialNews.isEmpty)
                )

                AIInsightCard(
                    insight: viewModel.state.aiDailyInsight,
                    state: cardState(hasContent: viewModel.state.aiDailyInsight != nil)
                )

                WatchlistCard(
                    watchlists: viewModel.state.watchlists,
                    state: cardState(hasContent: !viewModel.state.watchlists.isEmpty)
                )

                PerformanceChartCard(
                    chart: viewModel.state.recentPortfolioPerformance,
                    state: cardState(hasContent: viewModel.state.recentPortfolioPerformance != nil)
                )

                QuickActionsCard(state: cardState(hasContent: true), onRefresh: refresh)
            }
            .animation(.easeInOut(duration: 0.24), value: viewModel.loadingState)
        }
        .scrollIndicators(.hidden)
    }

    private func cardState(hasContent: Bool) -> DashboardCardState {
        switch viewModel.loadingState {
        case .idle, .loading:
            .loading
        case .loaded:
            hasContent ? .loaded : .empty
        case .failed(let message):
            .failed(message)
        }
    }

    private func refresh() {
        Task { await viewModel.refresh() }
    }
}

#if DEBUG
#Preview("Dashboard - Loading") {
    DashboardView(viewModel: DashboardPreviewFactory.make(state: .loading))
        .frame(width: 1024, height: 760)
}

#Preview("Dashboard - Loaded") {
    DashboardView(viewModel: DashboardPreviewFactory.make(state: .loaded))
        .frame(width: 1280, height: 800)
}

#Preview("Dashboard - Empty") {
    DashboardView(viewModel: DashboardPreviewFactory.make(state: .empty))
        .frame(width: 1440, height: 900)
}

#Preview("Dashboard - Error") {
    DashboardView(viewModel: DashboardPreviewFactory.make(state: .failed("Preview error")))
        .frame(width: 800, height: 600)
}
#endif
