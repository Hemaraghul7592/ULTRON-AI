import SwiftUI

public struct PortfolioWorkspaceSummaryCard: View {
    let summary: PortfolioSummary?
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Portfolio Summary", subtitle: "Authoritative values from PortfolioEngine", icon: "briefcase.fill", tint: .blue, state: state) {
            VStack(alignment: .leading, spacing: 16) {
                Text(summary?.totalValue.formatted(.currency(code: "USD")) ?? "Unavailable")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                HStack(spacing: 18) {
                    WorkspaceMetric(label: "Today's Gain/Loss", value: summary?.dayChange.formatted(.currency(code: "USD")) ?? "Unavailable", tint: .green)
                    WorkspaceMetric(label: "Cash Balance", value: summary?.cashBalance.formatted(.currency(code: "USD")) ?? "Unavailable", tint: .blue)
                    WorkspaceMetric(label: "Unrealized P/L", value: summary?.totalReturn.formatted(.currency(code: "USD")) ?? "Unavailable", tint: .orange)
                    WorkspaceMetric(label: "Realized P/L", value: "Unavailable", tint: .secondary)
                }
            }
        }
    }
}

struct WorkspaceMetric: View {
    let label: String
    let value: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(label.uppercased())
                .font(.system(size: 9, weight: .semibold))
                .foregroundStyle(.secondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(tint)
                .lineLimit(1)
        }
        .accessibilityElement(children: .combine)
    }
}
