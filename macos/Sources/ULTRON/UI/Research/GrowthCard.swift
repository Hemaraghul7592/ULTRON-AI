import SwiftUI

public struct GrowthCard: View {
    let fundamental: ResearchFundamentalState; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Growth", subtitle: "Historical financial trends", icon: "chart.line.uptrend.xyaxis", tint: .green, state: state) { VStack(spacing: 9) { row("Revenue Growth", fundamental.growth?.revenueGrowth); row("EPS Growth", fundamental.growth?.epsGrowth); row("Cash Flow Growth", fundamental.growth?.fcfGrowth); row("Historical Trend", fundamental.growth == nil ? nil : "Available") } } }
    private func row(_ label: String, _ value: Double?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value?.formatted(.percent) ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
