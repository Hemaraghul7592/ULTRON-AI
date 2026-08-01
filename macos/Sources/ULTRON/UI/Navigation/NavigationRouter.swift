import SwiftUI

/// Navigation destinations in the sidebar.
public enum NavItem: String, CaseIterable, Identifiable {
    case dashboard, markets, portfolio, watchlists, charts, research
    case sebi, copilot, aiAdvisor, alerts, settings

    public var id: String { rawValue }
    public var label: String { rawValue.capitalized }
    public var icon: String {
        switch self {
        case .dashboard: "square.grid.2x2"; case .markets: "chart.line.uptrend.xyaxis"
        case .portfolio: "briefcase"; case .watchlists: "eye"
        case .charts: "chart.bar"; case .research: "magnifyingglass"
        case .sebi: "building.columns"; case .copilot: "brain.head.profile"
        case .aiAdvisor: "message"; case .alerts: "bell"; case .settings: "gear"
        }
    }
}
