import SwiftUI

public struct FinancialHealthCard: View {
    let fundamental: ResearchFundamentalState; let state: DashboardCardState
    public var body: some View { DashboardCard(title: "Financial Health", subtitle: "Liquidity, leverage, efficiency, and cash flow", icon: "heart.text.square.fill", tint: .mint, state: state) { VStack(spacing: 9) { row("Liquidity", nil); row("Leverage", nil); row("Efficiency", nil); row("Cash Flow", fundamental.growth == nil ? nil : "Available"); row("Debt", nil); row("Overall Health", fundamental.score?.rating.rawValue.capitalized) } } }
    private func row(_ label: String, _ value: String?) -> some View { HStack { Text(label).font(.caption).foregroundStyle(.secondary); Spacer(); Text(value ?? "Unavailable").font(.caption.weight(.semibold)).foregroundStyle(value == nil ? .tertiary : .primary) } }
}
