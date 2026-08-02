import SwiftUI

public struct PortfolioAnalyticsCard: View {
    let analytics: PortfolioAnalytics
    let state: DashboardCardState

    public var body: some View {
        DashboardCard(title: "Portfolio Analytics", subtitle: "Risk and diversification signals", icon: "dial.medium.fill", tint: .mint, state: state) {
            VStack(alignment: .leading, spacing: 9) {
                analyticsRow("Diversification Score", analytics.diversificationScore.map { $0.formatted(.number.precision(.fractionLength(0))) })
                analyticsRow("Largest Holding", analytics.largestHolding)
                analyticsRow("Sector Allocation", analytics.sectorAllocationAvailable ? "Available" : nil)
                analyticsRow("Risk Estimate", analytics.riskEstimate.map { $0.formatted(.number.precision(.fractionLength(1))) })
                analyticsRow("Annualized Return", analytics.annualizedReturn.map { $0.formatted(.percent) })
                analyticsRow("Max Drawdown", analytics.maxDrawdown.map { $0.formatted(.percent) })
                analyticsRow("Portfolio CAGR", analytics.cagr.map { $0.formatted(.percent) })
            }
        }
    }

    private func analyticsRow(_ label: String, _ value: String?) -> some View {
        HStack {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(value ?? "Unavailable")
                .font(.caption.weight(.semibold))
                .foregroundStyle(value == nil ? .tertiary : .primary)
        }
    }
}
