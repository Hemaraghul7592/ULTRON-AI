import SwiftUI

/// Main application shell with sidebar navigation.
public struct AppShell: View {
    private let compositionRoot: ApplicationCompositionRoot
    @State private var selection: NavItem = .dashboard
    @State private var searchText = ""
    @State private var dashboardViewModel: DashboardViewModel?
    @State private var portfolioWorkspaceViewModel: PortfolioWorkspaceViewModel?
    @State private var marketWorkspaceViewModel: MarketWorkspaceViewModel?
    @State private var researchWorkspaceViewModel: ResearchWorkspaceViewModel?
    @State private var aiWorkspaceViewModel: AIWorkspaceViewModel?

    public init(compositionRoot: ApplicationCompositionRoot) {
        self.compositionRoot = compositionRoot
    }

    public var body: some View {
        NavigationSplitView {
            sidebar
        } detail: {
            detailView
        }
        .searchable(text: $searchText, placement: .sidebar, prompt: "Search stocks, symbols, filings...")
        .navigationTitle("ULTRON")
        .animation(.easeInOut(duration: 0.2), value: selection)
        .preferredColorScheme(.dark)
        .task {
            guard dashboardViewModel == nil else { return }
            dashboardViewModel = try? await compositionRoot.resolve(DashboardViewModel.self)
            portfolioWorkspaceViewModel = try? await compositionRoot.resolve(PortfolioWorkspaceViewModel.self)
            marketWorkspaceViewModel = try? await compositionRoot.resolve(MarketWorkspaceViewModel.self)
            researchWorkspaceViewModel = try? await compositionRoot.resolve(ResearchWorkspaceViewModel.self)
            aiWorkspaceViewModel = try? await compositionRoot.resolve(AIWorkspaceViewModel.self)
        }
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
        case .dashboard:
            if let dashboardViewModel {
                DashboardView(viewModel: dashboardViewModel)
            } else {
                ProgressView("Loading dashboard...")
            }
        case .markets:
            if let marketWorkspaceViewModel {
                MarketWorkspaceView(viewModel: marketWorkspaceViewModel)
            } else {
                ProgressView("Loading market...")
            }
        case .portfolio:
            if let portfolioWorkspaceViewModel {
                PortfolioWorkspaceView(viewModel: portfolioWorkspaceViewModel)
            } else {
                ProgressView("Loading portfolio...")
            }
        case .watchlists: WatchlistView()
        case .charts: ChartsView()
        case .research:
            if let researchWorkspaceViewModel {
                ResearchWorkspaceView(viewModel: researchWorkspaceViewModel)
            } else {
                ProgressView("Loading research...")
            }
        case .sebi: SEBIDetailView()
        case .copilot: CopilotView()
        case .aiAdvisor:
            if let aiWorkspaceViewModel {
                AIWorkspaceView(viewModel: aiWorkspaceViewModel)
            } else {
                ProgressView("Loading AI workspace...")
            }
        case .alerts: AlertsView()
        case .settings: SettingsView()
        }
    }
}
