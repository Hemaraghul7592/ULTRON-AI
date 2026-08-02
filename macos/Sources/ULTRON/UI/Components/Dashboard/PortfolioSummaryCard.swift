import SwiftUI

public struct PortfolioSummaryCard: View {
    private let summary: PortfolioSummary?
    private let state: DashboardCardState

    public init(summary: PortfolioSummary?, state: DashboardCardState) {
        self.summary = summary
        self.state = state
    }

    public var body: some View {
        DashboardCard(title: "Portfolio Summary", subtitle: "Across your active portfolio", icon: "briefcase.fill", tint: .blue, state: state) {
            VStack(alignment: .leading, spacing: 14) {
                Text(summary?.totalValue.formatted(.currency(code: "USD")) ?? "Unavailable")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                    .contentTransition(.numericText())

                HStack(spacing: 12) {
                    MetricChip(label: "Return", value: summary?.totalReturnPercent.formatted(.percent) ?? "Unavailable", tint: .green)
                    MetricChip(label: "Cash", value: summary?.cashBalance.formatted(.currency(code: "USD")) ?? "Unavailable", tint: .blue)
                    MetricChip(label: "Holdings", value: summary.map { "\($0.holdingsCount)" } ?? "Unavailable", tint: .purple)
                }
            }
        }
    }
}

struct MetricChip: View {
    let label: String
    let value: String
    let tint: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
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
