import SwiftUI

public struct RiskCard: View {
    let exposure: PortfolioSummary?; let analysis: AdvisorResponse?; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Risk Analysis", subtitle: "Existing portfolio and advisor context", icon: "exclamationmark.shield.fill", tint: .red, state: state) { VStack(spacing: 9) { row("Volatility", nil); row("Trend Risk", analysis?.risks.isEmpty == false ? "Observed" : nil); row("Portfolio Exposure", exposure?.totalValue.formatted(.currency(code: "USD"))); row("Diversification Impact", nil); row("AI Risk Summary", analysis?.risks.isEmpty == false ? "Available" : nil) } } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
