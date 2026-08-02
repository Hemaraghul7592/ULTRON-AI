import SwiftUI

public struct MarketOverviewCard: View {
    private let status: DashboardMarketStatus
    private let state: DashboardCardState

    public init(status: DashboardMarketStatus, state: DashboardCardState) {
        self.status = status
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Market Overview", subtitle: "Live provider availability", icon: "chart.line.uptrend.xyaxis", tint: .green, state: state) {
            HStack(spacing: 14) {
                Image(systemName: status == .available ? "checkmark.circle.fill" : "minus.circle")
                    .font(.title)
                    .foregroundStyle(status == .available ? .green : .secondary)
                VStack(alignment: .leading, spacing: 4) {
                    Text(status.rawValue)
                        .font(.title3.weight(.semibold))
                    Text(status == .available ? "Market data is responding." : "Market data is not available.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}
