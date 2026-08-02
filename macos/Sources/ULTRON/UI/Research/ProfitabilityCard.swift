import SwiftUI

public struct ProfitabilityCard: View {
    let fundamental: ResearchFundamentalState; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Profitability", subtitle: "Margins and returns", icon: "percent", tint: .orange, state: state) { VStack(spacing: 9) { row("ROE", fundamental.profitability?.roe); row("ROA", fundamental.profitability?.roa); row("Gross Margin", fundamental.profitability?.grossMargin); row("Operating Margin", fundamental.profitability?.operatingMargin); row("Net Margin", fundamental.profitability?.netMargin) } } }
    private func row(_ label: String, _ value: Double?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value?.formatted(.percent) ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
