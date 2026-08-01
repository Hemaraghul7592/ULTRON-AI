import SwiftUI

/// Main application shell with sidebar navigation.
public struct AppShell: View {
    @State private var selection: NavItem = .dashboard
    @State private var searchText = ""

    public init() {}

    public var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            detailView
        }
        .searchable(text: $searchText, placement: .sidebar, prompt: "Search stocks, symbols, filings...")
        .navigationTitle("ULTRON")
    }

    private var sidebar: some View {
        List(NavItem.allCases, selection: $selection) { item in
            Label(item.label, systemImage: item.icon)
                .tag(item)
        }
        .listStyle(.sidebar)
        .frame(minWidth: 200)
    }

    @ViewBuilder
    private var detailView: some View {
        switch selection {
        case .dashboard: DashboardView()
        case .markets: MarketView()
        case .portfolio: PortfolioView()
        case .watchlists: WatchlistView()
        case .charts: ChartsView()
        case .research: ResearchView()
        case .sebi: SEBIDetailView()
        case .copilot: CopilotView()
        case .aiAdvisor: AIChatView()
        case .alerts: AlertsView()
        case .settings: SettingsView()
        }
    }
}
